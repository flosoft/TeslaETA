import { TestBed } from '@angular/core/testing';
import { Subject } from 'rxjs';

import { WsService } from './ws.service';
import { StateDTO } from '../../../dtos/state-dto';

describe('WsService', () => {
  let service: WsService;

  const mockSocketFactory = () => {
    const subject = new Subject<StateDTO>() as any;
    subject.complete = jasmine.createSpy('complete');
    return subject;
  };

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(WsService);
  });

  afterEach(() => {
    service.ngOnDestroy();
  });

  it('should emit state updates received from server', (done) => {
    const mockState: StateDTO = {
      latitude: 1, longitude: 2, odometer: 100,
      is_driving: true, is_charging: false, battery_level: 90
    };

    const socketSubject = mockSocketFactory();
    spyOn(service as any, 'createSocket').and.returnValue(socketSubject);

    service.connect('test-uuid').subscribe(state => {
      expect(state).toEqual(mockState);
      done();
    });

    socketSubject.next(mockState);
  });

  it('should set connected as true when socket opens', (done) => {
    let capturedConfig: any;
    const socketSubject = mockSocketFactory();
    spyOn(service as any, 'createSocket').and.callFake((config: any) => {
      capturedConfig = config;
      return socketSubject;
    });

    service.connect('test-uuid').subscribe();
    service.connected$.subscribe(connected => {
      if (connected) {
        expect(connected).toBeTrue();
        done();
      }
    });

    capturedConfig.openObserver.next();
  });

  it('should set connected as false when socket closes', (done) => {
    let capturedConfig: any;
    const socketSubject = mockSocketFactory();
    spyOn(service as any, 'createSocket').and.callFake((config: any) => {
      capturedConfig = config;
      return socketSubject;
    });

    service.connect('test-uuid').subscribe();
    service.connected$.subscribe(connected => {
      if (connected === false) {
        expect(connected).toBeFalse();
        done();
      }
    });

    capturedConfig.closeObserver.next();
  });
});
