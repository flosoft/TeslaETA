import { Injectable, OnDestroy } from '@angular/core';
import { Observable, Subject, timer } from 'rxjs';
import { webSocket, WebSocketSubject, WebSocketSubjectConfig } from 'rxjs/webSocket';
import { retry, tap } from 'rxjs/operators';
import { StateDTO } from '../../../dtos/state-dto';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class WsService implements OnDestroy {
  private socket$?: WebSocketSubject<StateDTO>;
  private _connected$ = new Subject<boolean>();
  public connected$ = this._connected$.asObservable();

  connect(shortuuid: string): Observable<StateDTO> {
    this.disconnect();
    const base = environment.wsUrl || this._deriveWsBase();
    this.socket$ = this.createSocket({
      url: `${base}/ws/${shortuuid}`,
      deserializer: (event) => JSON.parse(event.data) as StateDTO,
      openObserver: { next: () => this._connected$.next(true) },
      closeObserver: { next: () => this._connected$.next(false) },
    });

    return this.socket$.pipe(
      tap({ error: () => this._connected$.next(false) }),
      retry({
        count: 20,
        delay: (_, retryCount) => timer(Math.min(1000 * Math.pow(2, retryCount - 1), 30_000))
      })
    );
  }

  protected createSocket(config: WebSocketSubjectConfig<StateDTO>): WebSocketSubject<StateDTO> {
    return webSocket<StateDTO>(config);
  }

  private _deriveWsBase(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}`;
  }

  disconnect(): void {
    this.socket$?.complete();
    this.socket$ = undefined;
  }

  ngOnDestroy(): void {
    this.disconnect();
    this._connected$.complete();
  }
}

