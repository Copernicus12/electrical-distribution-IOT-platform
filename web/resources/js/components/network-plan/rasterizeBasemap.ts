export type BasemapRaster = {
    image: ImageBitmap;
    width: number;
    height: number;
    dispose: () => void;
};

/**
 * Flatten only the static cartography. Markers, connections and popups remain
 * interactive vectors, while navigation no longer retessellates every building.
 */
export async function rasterizeBasemap(
    layer: SVGGElement,
    width: number,
    height: number,
): Promise<BasemapRaster> {
    const snapshot = document.createElementNS(
        'http://www.w3.org/2000/svg',
        'svg',
    );
    snapshot.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    snapshot.setAttribute('width', String(width));
    snapshot.setAttribute('height', String(height));
    snapshot.setAttribute('viewBox', '0 0 ' + width + ' ' + height);
    const copy = layer.cloneNode(true) as SVGGElement;
    const originalText = layer.querySelectorAll('text');
    const copiedText = copy.querySelectorAll('text');
    const textProperties = [
        'fill',
        'stroke',
        'stroke-width',
        'font-family',
        'font-size',
        'font-weight',
        'font-style',
        'letter-spacing',
        'paint-order',
    ];
    originalText.forEach((element, index) => {
        const style = getComputedStyle(element);
        for (const property of textProperties) {
            copiedText[index].style.setProperty(
                property,
                style.getPropertyValue(property),
            );
        }
    });
    snapshot.append(copy);
    const url = URL.createObjectURL(
        new Blob([new XMLSerializer().serializeToString(snapshot)], {
            type: 'image/svg+xml;charset=utf-8',
        }),
    );
    const source = new Image();
    try {
        source.src = url;
        await source.decode();
        const canvas = document.createElement('canvas');
        // Keep the cached layer bounded to about 42 MB, including on Retina screens.
        canvas.width = 4096;
        canvas.height = Math.round((canvas.width * height) / width);
        const context = canvas.getContext('2d', { alpha: false });
        if (!context) throw new Error('A 2D canvas context is required.');
        context.drawImage(source, 0, 0, canvas.width, canvas.height);
        const image = await createImageBitmap(canvas);
        canvas.width = canvas.height = 1;
        return {
            image,
            width: image.width,
            height: image.height,
            dispose: () => image.close(),
        };
    } finally {
        URL.revokeObjectURL(url);
        source.src = '';
    }
}
