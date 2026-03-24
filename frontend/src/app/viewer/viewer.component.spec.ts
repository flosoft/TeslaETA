import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { Subject, of } from 'rxjs';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButton, MatButtonModule } from '@angular/material/button';

import { ViewerComponent } from './viewer.component';
import { ApiService } from '../services/api/api.service';
import { WsService } from '../services/ws/ws.service';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { StateDTO } from '../../dtos/state-dto';

describe('ViewerComponent', () => {
  let component: ViewerComponent;
  let fixture: ComponentFixture<ViewerComponent>;
  let apiServiceSpy: jasmine.SpyObj<ApiService>;
  let wsServiceSpy: jasmine.SpyObj<WsService>;
  let routerSpy: jasmine.SpyObj<Router>;
  let wsMessages$: Subject<StateDTO>;
  let wsConnected$: Subject<boolean>;

  const mockState: StateDTO = {
    latitude: 0, longitude: 0, odometer: 0,
    is_driving: false, is_charging: false, battery_level: 0
  };

  beforeEach(async () => {
    wsMessages$ = new Subject<StateDTO>();
    wsConnected$ = new Subject<boolean>();

    apiServiceSpy = jasmine.createSpyObj('ApiService', ['getState']);
    wsServiceSpy = jasmine.createSpyObj('WsService', ['connect', 'disconnect'], {
      connected$: wsConnected$.asObservable()
    });
    routerSpy = jasmine.createSpyObj('Router', [], { url: '/test-uuid' });

    apiServiceSpy.getState.and.returnValue(of(mockState));
    wsServiceSpy.connect.and.returnValue(wsMessages$.asObservable());

    await TestBed.configureTestingModule({
      imports: [ViewerComponent],
      providers: [
        { provide: ApiService, useValue: apiServiceSpy },
        { provide: WsService, useValue: wsServiceSpy },
        { provide: Router, useValue: routerSpy },
        { provide: HttpClient, useValue: jasmine.createSpyObj('HttpClient', ['get']) },
      ],
    })
      .overrideComponent(ViewerComponent, {
        set: {
          imports: [CommonModule, MatCardModule, MatButtonModule, MatButton],
          schemas: [NO_ERRORS_SCHEMA]
        }
      })
      .compileComponents();

    fixture = TestBed.createComponent(ViewerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should subscribe to WebSocket service on init', () => {
    expect(wsServiceSpy.connect).toHaveBeenCalledWith('test-uuid');
  });

  it('should call updateState when WS message received', () => {
    spyOn(component, 'updateState');
    const state: StateDTO = {
      latitude: 10, longitude: 20, odometer: 100,
      is_driving: true, is_charging: false, battery_level: 80
    };
    wsMessages$.next(state);
    expect(component.updateState).toHaveBeenCalledWith(state);
  });

  it('should disconnect WS on destroy', () => {
    component.ngOnDestroy();
    expect(wsServiceSpy.disconnect).toHaveBeenCalled();
  });

  describe('mapLoad', () => {
    let mockMap: any;

    beforeEach(() => {
      mockMap = {
        loadImage: jasmine.createSpy('loadImage').and.callFake((_url: string, cb: Function) => cb(null, {})),
        addImage: jasmine.createSpy('addImage'),
        addSource: jasmine.createSpy('addSource'),
        addLayer: jasmine.createSpy('addLayer'),
        getSource: jasmine.createSpy('getSource').and.returnValue({ setData: jasmine.createSpy('setData') }),
        on: jasmine.createSpy('on'),
        flyTo: jasmine.createSpy('flyTo'),
      };
      component.map = mockMap;
    });

    it('should register car-arrow image via loadImage', () => {
      component.mapLoad({});
      expect(mockMap.addImage).toHaveBeenCalledWith('car-arrow', jasmine.any(Object));
    });

    it('layer-with-car-arrow should have icon-rotate expression in layout', () => {
      component.mapLoad({});
      const layerArg = mockMap.addLayer.calls.first().args[0];
      expect(layerArg.id).toBe('layer-with-car-arrow');
      expect(layerArg.layout['icon-rotate']).toEqual(['get', 'heading']);
    });

    it('should add source with id car-arrow', () => {
      component.mapLoad({});
      expect(mockMap.addSource).toHaveBeenCalledWith('car-arrow', jasmine.any(Object));
    });
  });

  describe('updateState heading', () => {
    let mockSource: any;
    let mockMap: any;

    beforeEach(() => {
      mockSource = { setData: jasmine.createSpy('setData') };
      mockMap = {
        loadImage: jasmine.createSpy('loadImage').and.callFake((_url: string, cb: Function) => cb(null, {})),
        addImage: jasmine.createSpy('addImage'),
        addSource: jasmine.createSpy('addSource'),
        addLayer: jasmine.createSpy('addLayer'),
        getSource: jasmine.createSpy('getSource').and.returnValue(mockSource),
        on: jasmine.createSpy('on'),
        flyTo: jasmine.createSpy('flyTo'),
      };
      component.map = mockMap;
    });

    it('should pass heading: 0 in properties when state.heading is undefined', () => {
      const state: StateDTO = { ...mockState };
      component.updateState(state);
      const featureArg = mockSource.setData.calls.first().args[0];
      expect(featureArg.properties.heading).toBe(0);
    });

    it('should pass heading: 90 in properties when state.heading is 90', () => {
      const state: StateDTO = { ...mockState, heading: 90 };
      component.updateState(state);
      const featureArg = mockSource.setData.calls.first().args[0];
      expect(featureArg.properties.heading).toBe(90);
    });
  });
});
