
export class StateDTO {
    latitude!: number
    longitude!: number
    odometer!: number
    is_driving!: Boolean
    is_charging!: Boolean
    shift_state?: string
    battery_level!: number
    heading?: number
    speed?: number

    active_route_destination?: string
    active_route_latitude?: number
    active_route_longitude?: number
    active_route_minutes_to_arrival?: number
    active_route_energy_at_arrival?: number
}
