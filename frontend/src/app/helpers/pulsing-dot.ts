

export class PulsingDot {
    constructor(private map: mapboxgl.Map) { }

    private size = 100;
    private context?: CanvasRenderingContext2D | null


    width = this.size
    height = this.size
    data = new Uint8ClampedArray(this.size * this.size * 4)


    // When the layer is added to the map,
    // get the rendering context for the map canvas.
    onAdd(): void {
        console.log("ADDED")
        const canvas = document.createElement('canvas');
        canvas.width = this.size;
        canvas.height = this.size;
        this.context = canvas.getContext('2d');
    }

    // Call once before every frame where the icon will be used.
    render(): boolean {
        const duration = 1000;
        const t = (performance.now() % duration) / duration;

        const radius = (this.size / 2) * 0.3;
        const outerRadius = (this.size / 2) * 0.7 * t + radius;
        const context = this.context;

        // Draw the outer circle.
        this.context!.clearRect(0, 0, this.size, this.size);
        context!.beginPath();
        context!.arc(
            this.size / 2,
            this.size / 2,
            outerRadius,
            0,
            Math.PI * 2
        );

        this.context!.fillStyle = `rgba(255, 200, 200, ${1 - t})`;
        context?.fill();

        // Draw the inner circle.
        context?.beginPath();
        context?.arc(
            this.size / 2,
            this.size / 2,
            radius,
            0,
            Math.PI * 2
        );

        this.context!.fillStyle = 'rgba(255, 100, 100, 1)';
        context!.strokeStyle = 'white';
        context!.lineWidth = 2 + 4 * (1 - t);
        context!.fill();
        context!.stroke();

        // Update this image's data with data from the canvas.
        let dataBuffer = context!.getImageData(
            0,
            0,
            this.size,
            this.size
        ).data;

        this.data = dataBuffer

        // this.data = new Uint8Array(dataBuffer)

        // Continuously repaint the map, resulting
        // in the smooth animation of the dot.
        this.map.triggerRepaint();
        
        // Return `true` to let the map know that the image was updated.
        return true;
    }

}