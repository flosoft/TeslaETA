import { environment } from '../../environments/environment';
import { Component, OnInit, OnDestroy, AfterViewInit } from '@angular/core';
import * as mapboxgl from 'mapbox-gl';
import { MapboxOptions } from 'mapbox-gl';
import { NgxMapboxGLModule } from 'ngx-mapbox-gl';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { HttpClient } from '@angular/common/http';
import { MatButton, MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';
import { ApiService } from '../services/api/api.service';
import { WsService } from '../services/ws/ws.service';
import { Router } from '@angular/router';
import { StateDTO } from '../../dtos/state-dto';
import { Subscription } from 'rxjs';


@Component({
    selector: 'app-viewer',
    imports: [
        CommonModule,
        NgxMapboxGLModule,
        MatCardModule,
        MatIconModule,
        MatButtonModule,
        MatButton
    ],
    templateUrl: './viewer.component.html',
    styleUrl: './viewer.component.scss'
})
export class ViewerComponent implements OnInit, OnDestroy {
    map: mapboxgl.Map | undefined;
    mainRoute: any;

    public initialState?: StateDTO
    public currentState?: StateDTO

    public latestDestinationLat: number = 0
    public latestDestinationLng: number = 0

    mapIsInteracting = false
    mapIsCentering = false
    private _recenterTimer: ReturnType<typeof setTimeout> | null = null
    private readonly RECENTER_DELAY_MS = 5000

    private lastHeading: number = 0

    isConnected = false
    readonly gearStates = ['P', 'R', 'N', 'D'] as const
    private _wsSub?: Subscription
    private _connectedSub?: Subscription

    constructor(
        private _http: HttpClient,
        private _apiService: ApiService,
        private _wsService: WsService,
        private _router: Router
    ) { }


    ngOnInit(): void {
        const share_shortuuid = this._router.url.replace(/^\/|\/$/g, '');
        this._connectedSub = this._wsService.connected$.subscribe(connected => this.isConnected = connected);
        this.initAutoRefresh(share_shortuuid)

        this._apiService.getState(share_shortuuid).subscribe(state => { this.initialState = state; this.currentState = state })

    }

    mapCreate(event: mapboxgl.Map): void {
        this.map = event
        this.addMapInteractionsEvents()

    }

    addMapInteractionsEvents(): void {
        // movestart fires for BOTH user gestures and programmatic flyTo.
        // e.originalEvent is only present for genuine user input.
        this.map!.on('movestart', (e: any) => {
            if (e.originalEvent) {
                // User-initiated drag/pinch/scroll — pause auto-centering
                this.mapIsInteracting = true
                this.mapIsCentering = false
                // Cancel any pending recenter timer
                if (this._recenterTimer) {
                    clearTimeout(this._recenterTimer)
                    this._recenterTimer = null
                }
            } else {
                // Programmatic flyTo — mark as centering to block re-entry
                this.mapIsCentering = true
            }
        })

        // moveend fires when any movement (including flyTo) finishes
        this.map!.on('moveend', (e: any) => {
            this.mapIsCentering = false
            if (e.originalEvent) {
                // User finished a gesture — schedule auto-recenter after delay
                if (this._recenterTimer) clearTimeout(this._recenterTimer)
                this._recenterTimer = setTimeout(() => {
                    this.mapIsInteracting = false
                    this._recenterTimer = null
                    this.centerMapIfNotDragging()
                }, this.RECENTER_DELAY_MS)
            }
        })

        // zoomstart via scroll wheel / pinch also counts as user interaction
        this.map!.on('zoomstart', (e: any) => {
            if (e.originalEvent) {
                this.mapIsInteracting = true
                if (this._recenterTimer) {
                    clearTimeout(this._recenterTimer)
                    this._recenterTimer = null
                }
            }
        })
    }

    initAutoRefresh(share_shortuuid: string): void {
        this._wsSub = this._wsService.connect(share_shortuuid).subscribe({
            next: (state) => this.updateState(state),
            error: (err) => console.error('WS error:', err)
        });
    }

    ngOnDestroy(): void {
        this._wsSub?.unsubscribe();
        this._connectedSub?.unsubscribe();
        this._wsService.disconnect();
        if (this._recenterTimer) clearTimeout(this._recenterTimer);
    }

    mapLoad(event: any): void {
        this.map!.loadImage('/assets/car-arrow.png', (error: any, image: any) => {
            if (error) { console.error('Failed to load car-arrow.png', error); return; }

            this.map!.addImage('car-arrow', image);

            this.map!.addSource('car-arrow', {
                type: 'geojson',
                data: {
                    type: 'FeatureCollection',
                    features: [
                        {
                            type: 'Feature',
                            geometry: {
                                type: 'Point',
                                coordinates: [0, 0]
                            },
                            properties: { heading: 0 }
                        }
                    ]
                }
            });

            this.map!.addLayer({
                id: 'layer-with-car-arrow',
                type: 'symbol',
                source: 'car-arrow',
                layout: {
                    'icon-image': 'car-arrow',
                    'icon-size': 0.4,
                    'icon-rotate': ['get', 'heading'],
                    'icon-rotation-alignment': 'map',
                    'icon-allow-overlap': true,
                    'icon-ignore-placement': true,
                }
            });

            // If state was already received before the image finished loading, apply it now
            if (this.currentState) {
                this.updateState(this.currentState);
            }
        });
    }

    updateState(state: StateDTO): void {
        // Only update the initial state once. This is necessary for the center binding of the map
        if (this.initialState == undefined) {
            this.initialState = state
        }

        this.currentState = state

        if (state.active_route_latitude && state.active_route_longitude) {
            // If the last saved destination is different than the one sent by the API, re-calculate the route
            if (state.active_route_latitude != this.latestDestinationLat || state.active_route_longitude != this.latestDestinationLng) {
                this.map?.resize()
                this.loadDirectionGeometry(state.latitude, state.longitude, state.active_route_latitude, state.active_route_longitude)
                this.latestDestinationLat = state.active_route_latitude
                this.latestDestinationLng = state.active_route_longitude

                console.log("Re-calculated routing")
            }
        }

        if (!this.map) {
            return
        }

        this.centerMapIfNotDragging()

        let newSourceData : GeoJSON.Feature<GeoJSON.Geometry> = {
            type: 'Feature',
            geometry: {
                type: 'Point',
                coordinates: [state.longitude, state.latitude]
            },
            properties: { heading: state.heading ?? this.lastHeading }
        }
        if (state.heading != null) {
            this.lastHeading = state.heading
        }

        const sourceToUpdate = this.map!.getSource("car-arrow") as mapboxgl.GeoJSONSource
        sourceToUpdate?.setData(newSourceData)
    }

    centerMapIfNotDragging(): void {
        if (!this.map) return
        if (this.mapIsInteracting || this.mapIsCentering) return
        this.map.flyTo({
            center: [this.currentState!.longitude, this.currentState!.latitude],
            essential: true,
            zoom: 15,
            speed: 0.8,
            maxDuration: 2000
        })
    }

    get minutesToArrival(): string {
        const mins = this.currentState?.active_route_minutes_to_arrival;
        if (mins == null) return '--';
        const total = Math.round(mins);
        if (total < 60) return `${total} min`;
        const h = Math.floor(total / 60);
        const m = total % 60;
        return m > 0 ? `${h} h ${m} min` : `${h} h`;
    }

    loadDirectionGeometry(startLat: number, startLng: number, endLat: number, endLng: number): void {
        let mapboxApiPrefix = "https://api.mapbox.com/directions/v5/mapbox/driving"

        this._http.get<any>(`${mapboxApiPrefix}/${startLng},${startLat};${endLng},${endLat}?access_token=${environment.mapboxToken}&geometries=geojson&overview=full`)
            .subscribe(res => {
                this.mainRoute = {
                    type: 'geojson',
                    data: {
                        type: 'Feature',
                        properties: {},
                        geometry: res.routes[0].geometry
                    }
                }
            })
    }
}
