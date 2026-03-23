import { environment } from '../../environments/environment';
import { Component, OnInit, AfterViewInit, } from '@angular/core';
import * as mapboxgl from 'mapbox-gl';
import { MapboxOptions } from 'mapbox-gl';
import { NgxMapboxGLModule } from 'ngx-mapbox-gl';
import { MatCardModule } from '@angular/material/card';
import { HttpClient } from '@angular/common/http';
import { MatButton, MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';
import { ApiService } from '../services/api/api.service';
import { Router } from '@angular/router';
import { StateDTO } from '../../dtos/state-dto';
import { catchError, of, share, switchMap, timer } from 'rxjs';
import { PulsingDot } from '../helpers/pulsing-dot';


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
export class ViewerComponent {
    map: mapboxgl.Map | undefined;
    mainRoute: any;

    public initialState?: StateDTO
    public currentState?: StateDTO

    public latestDestinationLat: number = 0
    public latestDestinationLng: number = 0

    mapIsInteracting = false
    mapIsCentering = false

    public pulsingDot?: PulsingDot
    public pulsingDotSource?: mapboxgl.GeoJSONSourceRaw


    constructor(
        private _http: HttpClient,
        private _apiService: ApiService,
        private _router: Router
    ) { }


    ngOnInit(): void {
        const share_shortuuid = this._router.url.replace(/^\/|\/$/g, '');
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
        // Start a timer for auto-refreshing the state
        timer(0, 500).pipe(
            switchMap(() => this._apiService.getState(share_shortuuid)),
        ).subscribe(result => this.updateState(result))
    }

    mapLoad(event: any): void {
        this.pulsingDot = new PulsingDot(this.map!)

        this.map!.addImage('pulsing-dot', this.pulsingDot!, {pixelRatio: 1})

        this.pulsingDotSource = {
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
                        properties: null
                    }
                ]
            }
        }

        this.map!.addSource('pulsing-dot', this.pulsingDotSource!);

        this.map!.addLayer({
            id: 'layer-with-pulsing-dot',
            type: 'symbol',
            source: 'pulsing-dot',
            layout: {
                'icon-image': 'pulsing-dot',
            //   'icon-size': 0.25
            }
        });

        // this.map.
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

        this.centerMapIfNotDragging()

        let newSourceData : GeoJSON.Feature<GeoJSON.Geometry> = {
            type: 'Feature',
            geometry: {
                type: 'Point',
                coordinates: [state.longitude, state.latitude]
            },
            properties: {}
        }

        let sourceToUpdate = this.map!.getSource("pulsing-dot") as mapboxgl.GeoJSONSource
        sourceToUpdate.setData(newSourceData)
    }

    centerMapIfNotDragging(): void {
        if (!this.mapIsInteracting && !this.mapIsCentering) {
            this.map!.flyTo({
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
