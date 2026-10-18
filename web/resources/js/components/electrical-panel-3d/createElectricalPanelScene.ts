import {
    ACESFilmicToneMapping,
    BoxGeometry,
    CanvasTexture,
    CatmullRomCurve3,
    Color,
    CylinderGeometry,
    DirectionalLight,
    DoubleSide,
    Group,
    HemisphereLight,
    InstancedMesh,
    Mesh,
    MeshBasicMaterial,
    MeshStandardMaterial,
    Object3D,
    PerspectiveCamera,
    PlaneGeometry,
    Scene,
    SphereGeometry,
    SRGBColorSpace,
    TubeGeometry,
    Vector3,
    WebGLRenderer,
} from 'three';
import type { BufferGeometry, Material } from 'three';
import { createConnectorSide } from './createConnectorSide';
import { createControlDoor } from './createControlDoor';

export type ElectricalPanelScene = {
    rotate: (yaw: number) => void;
    setRunning: (running: boolean) => void;
    refreshTheme: () => void;
    resize: () => void;
    dispose: () => void;
};

/** A cabinet made of actual solid geometry. No photograph or SVG is used. */
export function createElectricalPanelScene(
    host: HTMLElement,
): ElectricalPanelScene {
    const renderer = new WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    renderer.setClearColor(0, 0);
    renderer.toneMapping = ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1;
    renderer.domElement.setAttribute('aria-hidden', 'true');
    renderer.domElement.style.cssText =
        'display:block;width:100%;height:100%;pointer-events:none';
    host.appendChild(renderer.domElement);

    const scene = new Scene();
    const camera = new PerspectiveCamera(39, 1, 0.1, 30);
    camera.position.set(0, 0.12, 6.8);
    camera.lookAt(0, 0, 0);
    const pivot = new Group();
    const cabinet = new Group();
    cabinet.position.y = -1.38;
    pivot.add(cabinet);
    scene.add(pivot);

    const geometries = new Set<BufferGeometry>();
    const materials = new Set<Material>();
    const textures = new Set<CanvasTexture>();
    const cube = new BoxGeometry(1, 1, 1);
    geometries.add(cube);
    let disposed = false;
    let frame = 0;
    let powered = false;
    let statusColor = new Color();

    // Render on changes, rather than running four permanent animation loops.
    function render(): void {
        if (disposed || frame) return;
        frame = requestAnimationFrame(() => {
            frame = 0;
            if (!disposed) renderer.render(scene, camera);
        });
    }

    const metal = new MeshStandardMaterial({
        metalness: 0.45,
        roughness: 0.55,
    });
    const trim = new MeshStandardMaterial({ metalness: 0.65, roughness: 0.4 });
    const back = new MeshStandardMaterial({ metalness: 0.25, roughness: 0.75 });
    const terminal = new MeshStandardMaterial({ roughness: 0.75 });
    const duct = new MeshStandardMaterial({ roughness: 0.85 });
    const recess = new MeshStandardMaterial({ roughness: 0.9 });
    const wire = new MeshStandardMaterial({ roughness: 0.7 });
    const indicator = new MeshStandardMaterial({ roughness: 0.3 });
    const screen = new MeshStandardMaterial({ roughness: 0.5 });
    const segments = new MeshBasicMaterial();
    const glass = new MeshStandardMaterial({
        color: 0x959fa7,
        transparent: true,
        opacity: 0.09,
        roughness: 0.15,
        metalness: 0.1,
        depthWrite: false,
        side: DoubleSide,
    });
    [
        metal,
        trim,
        back,
        terminal,
        duct,
        recess,
        wire,
        indicator,
        screen,
        segments,
        glass,
    ].forEach((material) => materials.add(material));

    function box(
        parent: Group,
        size: [number, number, number],
        position: [number, number, number],
        material: Material,
    ): Mesh {
        const mesh = new Mesh(cube, material);
        mesh.scale.set(...size);
        mesh.position.set(...position);
        parent.add(mesh);
        return mesh;
    }

    function cable(
        parent: Group,
        points: [number, number, number][],
        radius = 0.006,
        material: Material = wire,
    ): void {
        const curve = new CatmullRomCurve3(
            points.map((point) => new Vector3(...point)),
        );
        const geometry = new TubeGeometry(curve, 18, radius, 5, false);
        geometries.add(geometry);
        parent.add(new Mesh(geometry, material));
    }

    function instances(
        parent: Group,
        size: [number, number, number],
        positions: [number, number, number][],
        material: Material,
    ): void {
        const mesh = new InstancedMesh(cube, material, positions.length);
        const transform = new Object3D();
        transform.scale.set(...size);
        positions.forEach((position, index) => {
            transform.position.set(...position);
            transform.updateMatrix();
            mesh.setMatrixAt(index, transform.matrix);
        });
        mesh.instanceMatrix.needsUpdate = true;
        parent.add(mesh);
    }

    // Solid shell: rear sheet, two deep side walls, roof, plinth and floor.
    box(cabinet, [1.2, 2.44, 0.035], [0, 1.48, -0.32], back);
    for (const x of [-0.6, 0.6]) {
        box(cabinet, [0.035, 2.45, 0.67], [x, 1.48, 0], metal);
        box(cabinet, [0.055, 2.46, 0.055], [x, 1.48, 0.34], trim);
        // Rear uprights and side reinforcement are visible when orbiting.
        box(cabinet, [0.055, 2.44, 0.055], [x, 1.48, -0.34], trim);
        for (const y of [0.5, 1.5, 2.5]) {
            box(cabinet, [0.016, 0.035, 0.56], [x * 0.96, y, 0], trim);
        }
    }
    box(cabinet, [1.25, 0.045, 0.73], [0, 2.72, 0], trim);
    box(cabinet, [1.24, 0.18, 0.72], [0, 0.16, 0], metal);
    box(cabinet, [1.17, 0.035, 0.65], [0, 0.32, 0], back);
    box(cabinet, [1.2, 0.055, 0.055], [0, 2.68, 0.34], trim);
    box(cabinet, [1.2, 0.055, 0.055], [0, 0.35, 0.34], trim);
    for (const x of [-0.47, 0.47]) {
        box(cabinet, [0.18, 0.06, 0.58], [x, 0.045, 0], recess);
    }
    // Folded seams and recessed access panel on the rear.
    box(cabinet, [1.03, 2.18, 0.012], [0, 1.48, -0.347], metal);
    for (const x of [-0.51, 0.51])
        box(cabinet, [0.012, 2.17, 0.015], [x, 1.48, -0.36], trim);

    // Mounting plate and slotted cable ducts inside the enclosure.
    box(cabinet, [1.06, 2.2, 0.025], [0, 1.5, -0.265], back);
    for (const x of [-0.49, 0.49]) {
        box(cabinet, [0.055, 2.03, 0.07], [x, 1.43, -0.17], duct);
    }
    const ductSlots: [number, number, number][] = [];
    for (let row = 0; row < 38; row++) {
        for (const x of [-0.49, 0.49])
            ductSlots.push([x, 0.46 + row * 0.052, -0.131]);
    }
    instances(cabinet, [0.033, 0.014, 0.007], ductSlots, recess);

    // Ten DIN rails, with separately instanced terminal bodies and sockets.
    const bodies: [number, number, number][] = [];
    const sockets: [number, number, number][] = [];
    const tabs: [number, number, number][] = [];
    for (let row = 0; row < 10; row++) {
        const y = 0.62 + row * 0.172;
        box(cabinet, [0.91, 0.034, 0.034], [0, y, -0.17], trim);
        box(cabinet, [0.91, 0.025, 0.065], [0, y - 0.081, -0.16], duct);
        for (let column = 0; column < 16; column++) {
            const x = -0.405 + column * 0.054;
            bodies.push([x, y, -0.105]);
            sockets.push([x, y - 0.026, -0.038], [x, y + 0.026, -0.038]);
            tabs.push([x, y - 0.065, -0.09], [x, y + 0.065, -0.09]);
        }
    }
    instances(cabinet, [0.047, 0.106, 0.13], bodies, terminal);
    instances(cabinet, [0.019, 0.019, 0.006], sockets, recess);
    instances(cabinet, [0.009, 0.024, 0.01], tabs, wire);

    // PM3255 analyzer: raised housing, recessed screen and real button geometry.
    box(cabinet, [0.34, 0.25, 0.12], [-0.29, 2.39, -0.11], recess);
    box(cabinet, [0.23, 0.105, 0.008], [-0.31, 2.385, -0.045], screen);
    for (const y of [2.367, 2.402]) {
        box(cabinet, [0.07, 0.004, 0.003], [-0.35, y, -0.039], segments);
        box(cabinet, [0.055, 0.004, 0.003], [-0.265, y, -0.039], segments);
    }
    for (let index = 0; index < 3; index++) {
        box(
            cabinet,
            [0.027, 0.018, 0.012],
            [-0.38 + index * 0.056, 2.3, -0.04],
            trim,
        );
    }
    // Keep the model identification on the analyzer, without a lower nameplate.
    const labelCanvas = document.createElement('canvas');
    labelCanvas.width = 256;
    labelCanvas.height = 48;
    const labelContext = labelCanvas.getContext('2d');
    if (labelContext) {
        labelContext.fillStyle = '#b1b5b8';
        labelContext.font = '26px sans-serif';
        labelContext.fillText('PM3255', 6, 34);
        const texture = new CanvasTexture(labelCanvas);
        texture.colorSpace = SRGBColorSpace;
        textures.add(texture);
        const labelMaterial = new MeshBasicMaterial({
            map: texture,
            transparent: true,
            depthWrite: false,
        });
        materials.add(labelMaterial);
        const geometry = new PlaneGeometry(0.25, 0.047);
        geometries.add(geometry);
        const label = new Mesh(geometry, labelMaterial);
        label.position.set(-0.29, 2.477, -0.045);
        cabinet.add(label);
    }
    const ledGeometry = new SphereGeometry(0.012, 8, 6);
    geometries.add(ledGeometry);
    for (const x of [0.015, 0.2, 0.385]) {
        box(cabinet, [0.145, 0.22, 0.1], [x, 2.39, -0.12], terminal);
        box(cabinet, [0.078, 0.08, 0.012], [x, 2.42, -0.064], recess);
        box(cabinet, [0.046, 0.012, 0.014], [x, 2.42, -0.055], trim);
        const led = new Mesh(ledGeometry, indicator);
        led.position.set(x, 2.32, -0.059);
        cabinet.add(led);
    }

    // Thick supply loop and lower protective-earth conductors have tube volume.
    cable(
        cabinet,
        [
            [0.17, 2.65, -0.19],
            [0.29, 2.54, -0.02],
            [0.32, 2.21, 0.02],
            [0.18, 2.18, 0.02],
            [0.13, 2.42, -0.02],
            [0.04, 2.64, -0.19],
        ],
        0.028,
        recess,
    );
    box(cabinet, [0.89, 0.025, 0.035], [0, 0.43, -0.1], trim);
    for (let index = 0; index < 9; index++) {
        const x = -0.38 + index * 0.095;
        cable(
            cabinet,
            [
                [x, 0.56, -0.05],
                [x, 0.5, -0.015],
                [x * 0.3, 0.4, 0.03],
            ],
            0.004,
        );
    }
    for (const x of [-0.12, -0.04, 0.04, 0.12]) {
        box(cabinet, [0.038, 0.14, 0.038], [x, 0.32, 0], recess);
    }

    // Solid two-sided control door, based on exterior/interior reference photos.
    createControlDoor(
        cabinet,
        { box, cable, geometries, materials, textures },
        {
            metal,
            trim,
            back,
            terminal,
            duct,
            recess,
            wire,
            indicator,
        },
    );

    createConnectorSide(
        cabinet,
        { box, cable, geometries, materials, textures },
        { metal, trim, back, terminal, duct, recess, wire, indicator },
    );

    // Right glass door: four solid frame members, thin glass and a raised handle.
    const rightDoor = new Group();
    rightDoor.position.set(0.615, 1.49, 0.36);
    rightDoor.rotation.y = (112 * Math.PI) / 180;
    cabinet.add(rightDoor);
    const rightWidth = 1.15;
    for (const x of [0, -rightWidth])
        box(rightDoor, [0.038, 2.35, 0.045], [x, 0, 0], metal);
    for (const y of [-1.155, 1.155])
        box(
            rightDoor,
            [rightWidth, 0.038, 0.045],
            [-rightWidth / 2, y, 0],
            metal,
        );
    box(rightDoor, [1.08, 2.27, 0.008], [-rightWidth / 2, 0, 0], glass);
    box(
        rightDoor,
        [0.035, 0.19, 0.05],
        [-rightWidth + 0.055, -0.04, 0.043],
        recess,
    );
    box(
        rightDoor,
        [0.015, 0.12, 0.022],
        [-rightWidth + 0.055, -0.04, 0.077],
        trim,
    );
    const hingeGeometry = new CylinderGeometry(0.023, 0.023, 0.08, 10);
    geometries.add(hingeGeometry);
    for (const x of [-0.61, 0.615]) {
        for (const y of [0.65, 1.5, 2.35]) {
            const hinge = new Mesh(hingeGeometry, trim);
            hinge.position.set(x, y, 0.36);
            cabinet.add(hinge);
        }
    }

    // A soft procedural contact shadow sits below the freely rotating object.
    const shadowCanvas = document.createElement('canvas');
    shadowCanvas.width = shadowCanvas.height = 64;
    const shadowContext = shadowCanvas.getContext('2d');
    if (shadowContext) {
        const gradient = shadowContext.createRadialGradient(
            32,
            32,
            2,
            32,
            32,
            31,
        );
        gradient.addColorStop(0, 'rgba(0,0,0,0.3)');
        gradient.addColorStop(1, 'rgba(0,0,0,0)');
        shadowContext.fillStyle = gradient;
        shadowContext.fillRect(0, 0, 64, 64);
        const texture = new CanvasTexture(shadowCanvas);
        textures.add(texture);
        const material = new MeshBasicMaterial({
            map: texture,
            transparent: true,
            depthWrite: false,
        });
        materials.add(material);
        const geometry = new PlaneGeometry(3, 2);
        geometries.add(geometry);
        const shadow = new Mesh(geometry, material);
        shadow.rotation.x = -Math.PI / 2;
        shadow.position.set(0, -1.385, 0.2);
        scene.add(shadow);
    }

    scene.add(new HemisphereLight(0xffffff, 0x343434, 2.1));
    for (const [x, y, z, intensity] of [
        [-3, 5, 5, 2.8],
        [4, 2, 3, 1.6],
        [0, 3, -4, 1.8],
    ]) {
        const light = new DirectionalLight(0xffffff, intensity);
        light.position.set(x, y, z);
        scene.add(light);
    }

    function readThemeColor(variable: string, fallback: number): Color {
        const probe = document.createElement('span');
        probe.style.color = `var(${variable})`;
        host.appendChild(probe);
        const value = getComputedStyle(probe).color;
        probe.remove();
        return value.startsWith('rgb') ? new Color(value) : new Color(fallback);
    }

    function setRunning(value: boolean): void {
        powered = value;
        indicator.color.copy(value ? statusColor : wire.color);
        indicator.emissive.copy(value ? statusColor : new Color(0));
        indicator.emissiveIntensity = value ? 0.6 : 0;
        screen.color.copy(
            value ? statusColor.clone().multiplyScalar(0.09) : recess.color,
        );
        segments.color.copy(
            value ? statusColor : wire.color.clone().multiplyScalar(0.2),
        );
        render();
    }

    function refreshTheme(): void {
        const dark = document.documentElement.classList.contains('dark');
        const foreground = readThemeColor(
            '--foreground',
            dark ? 0xfafafa : 0x0a0a0a,
        );
        const background = readThemeColor(
            '--background',
            dark ? 0x0a0a0a : 0xffffff,
        );
        const shade = (amount: number) =>
            background.clone().lerp(foreground, amount);
        metal.color.copy(shade(dark ? 0.12 : 0.42));
        trim.color.copy(shade(dark ? 0.28 : 0.22));
        back.color.copy(shade(dark ? 0.035 : 0.63));
        terminal.color.copy(shade(dark ? 0.2 : 0.3));
        duct.color.copy(shade(dark ? 0.065 : 0.55));
        recess.color.copy(shade(dark ? 0.006 : 0.94));
        wire.color.copy(shade(dark ? 0.36 : 0.76));
        statusColor = readThemeColor('--chart-2', 0x34b88a);
        setRunning(powered);
    }

    function resize(): void {
        if (disposed) return;
        const { width, height } = host.getBoundingClientRect();
        if (!width || !height) return;
        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        // Pull back on unusually narrow viewports, without enlarging the object.
        camera.position.z = 6.8 * Math.max(1, 320 / 450 / camera.aspect);
        camera.updateProjectionMatrix();
        render();
    }

    function rotate(yaw: number): void {
        // Horizontal orbit only: no pitch or roll from any input path.
        pivot.rotation.set(0, ((yaw - 10) * Math.PI) / 180, 0);
        render();
    }

    refreshTheme();
    rotate(0);
    resize();

    return {
        rotate,
        setRunning,
        refreshTheme,
        resize,
        dispose(): void {
            disposed = true;
            cancelAnimationFrame(frame);
            scene.traverse((object) => {
                if (object instanceof InstancedMesh) object.dispose();
            });
            geometries.forEach((geometry) => geometry.dispose());
            materials.forEach((material) => material.dispose());
            textures.forEach((texture) => texture.dispose());
            renderer.dispose();
            renderer.forceContextLoss();
            renderer.domElement.remove();
        },
    };
}
