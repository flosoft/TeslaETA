import { environment } from '../../environments/environment';
import { Component, OnInit, OnDestroy, AfterViewInit } from '@angular/core';
import * as mapboxgl from 'mapbox-gl';
import { MapboxOptions } from 'mapbox-gl';
import { NgxMapboxGLModule } from 'ngx-mapbox-gl';
import { MatCardModule } from '@angular/material/card';
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

    private lastHeading: number = 0

    isConnected = false
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
        // If the map becomes idle, enable the auto-center feature
        this.map!.on('idle', () => {
            this.mapIsInteracting = false
            console.log("MAP IS IDLE")
        })

        let interactEvents = ["click", "touchstart", "dragstart", "zoomstart"]
        interactEvents.forEach(ev => this.map!.on(ev, () => { this.mapIsInteracting = true; console.log("MAP INTERACTING") }))

        // this.map!.on('zo')
        this.map!.on('flyend', () => {
            this.mapIsCentering = false
        })

        this.map!.on('flystart', () => {
            this.mapIsCentering = true
        })

        // this.map!.on("dragstart", () => { console.log("DRAGGING HAS STARTED") })
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
        if (!this.mapIsInteracting && !this.mapIsCentering) {
            this.map.flyTo({
                center: [this.currentState!.longitude, this.currentState!.latitude],
                essential: true,
                zoom: 15,
                speed: 0.3,
                maxDuration: 5000
            })
        }
    }

    test(): void {
        this.map?.resize()
        this.loadDirectionGeometry(this.currentState!.latitude, this.currentState!.longitude, this.currentState!.active_route_latitude!, this.currentState!.active_route_longitude!)



        // this.map.d
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
