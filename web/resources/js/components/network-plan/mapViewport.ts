export type MapFrame = { x: number; y: number; width: number; height: number };
export type ViewportSize = { width: number; height: number };

export function mapZoomLimits(viewport: ViewportSize, bounds: MapFrame) {
    const aspect = Math.max(1, viewport.width) / Math.max(1, viewport.height);
    const maximum = Math.min(bounds.width, bounds.height * aspect);
    return { minimum: Math.min(400, maximum), maximum, aspect };
}

/** All input paths must use this constraint, including focus and resize. */
export function constrainMapFrame(
    requested: MapFrame,
    viewport: ViewportSize,
    bounds: MapFrame,
): MapFrame {
    const { minimum, maximum, aspect } = mapZoomLimits(viewport, bounds);
    const width = Math.max(minimum, Math.min(maximum, requested.width));
    const height = width / aspect;
    const centerX = requested.x + requested.width / 2;
    const centerY = requested.y + requested.height / 2;
    return {
        x: Math.max(
            bounds.x,
            Math.min(bounds.x + bounds.width - width, centerX - width / 2),
        ),
        y: Math.max(
            bounds.y,
            Math.min(bounds.y + bounds.height - height, centerY - height / 2),
        ),
        width,
        height,
    };
}
