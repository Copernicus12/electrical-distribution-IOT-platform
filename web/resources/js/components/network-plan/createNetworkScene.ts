import {
    ACESFilmicToneMapping,
    Box3,
    Box3Helper,
    BufferGeometry,
    Color,
    ConeGeometry,
    CurvePath,
    DirectionalLight,
    GridHelper,
    Group,
    HemisphereLight,
    Line,
    LineBasicMaterial,
    LineCurve3,
    LineDashedMaterial,
    Mesh,
    MeshBasicMaterial,
    PerspectiveCamera,
    Raycaster,
    Scene,
    TubeGeometry,
    Vector2,
    Vector3,
    WebGLRenderer,
} from 'three';
import type { Material, Object3D } from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { createNetworkModels } from './createNetworkModels';
import { supportLinkColor } from './networkColors';
import {
    assetById,
    networkAssets,
    networkConnections,
} from './networkTopology';
import type { NetworkConnection, Position } from './networkTopology';

export type PlanView = 'perspective' | 'top' | 'front';
export type ProjectedLabel = {
    id: string;
    x: number;
    y: number;
    visible: boolean;
};
export type NetworkScene = {
    resize: () => void;
    refreshTheme: () => void;
    setView: (view: PlanView) => void;
    zoom: (factor: number) => void;
    select: (id: string) => void;
    focus: (id: string) => void;
    showSupport: (visible: boolean) => void;
    handleKey: (event: KeyboardEvent) => void;
    dispose: () => void;
};

type SceneOptions = {
    onSelect: (id: string) => void;
    onProject: (labels: ProjectedLabel[]) => void;
};

export function createNetworkScene(
    host: HTMLElement,
    options: SceneOptions,
): NetworkScene {
    const renderer = new WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    renderer.setClearColor(0, 0);
    renderer.toneMapping = ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    renderer.domElement.style.cssText =
        'display:block;width:100%;height:100%;touch-action:none';
    renderer.domElement.setAttribute('aria-hidden', 'true');
    host.appendChild(renderer.domElement);

    const scene = new Scene();
    const camera = new PerspectiveCamera(40, 1, 0.1, 200);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = false;
    controls.minDistance = 6;
    controls.maxDistance = 85;
    controls.minPolarAngle = 0.04;
    controls.maxPolarAngle = Math.PI * 0.47;
    controls.maxTargetRadius = 24;
    const models = createNetworkModels();
    scene.add(models.createSite());
    const roots = new Map<string, Group>();
    for (const asset of networkAssets) {
        const root = models.createAsset(asset);
        roots.set(asset.id, root);
        scene.add(root);
    }
    const grid = new GridHelper(26, 26, 0x3d484e, 0x30393e);
    grid.position.set(0, 0.025, -1.5);
    scene.add(grid);
    scene.add(new HemisphereLight(0xe5f3ff, 0x43413b, 2.8));
    const key = new DirectionalLight(0xfff1d9, 3.4);
    key.position.set(-12, 22, 14);
    scene.add(key);
    const rim = new DirectionalLight(0xb4d9ff, 2.2);
    rim.position.set(12, 10, -12);
    scene.add(rim);

    const supply = new MeshBasicMaterial({ color: 0x6eaebc });
    const solar = new MeshBasicMaterial({ color: 0xc8a65b });
    const residential = new MeshBasicMaterial({ color: 0x648e86 });
    const support = new LineDashedMaterial({
        color: supportLinkColor,
        dashSize: 0.24,
        gapSize: 0.18,
        transparent: true,
        opacity: 0.95,
        toneMapped: false,
        depthWrite: false,
    });
    const supportGroup = new Group();
    supportGroup.visible = false;
    scene.add(supportGroup);
    const pickable = [...roots.values()];
    const arrowGeometry = new ConeGeometry(0.1, 0.3, 8);
    models.geometries.add(arrowGeometry);
    [supply, solar, residential, support].forEach((material) =>
        models.materials.add(material),
    );

    function route(connection: NetworkConnection, index: number): Vector3[] {
        const from = assetById.get(connection.from)!;
        const to = assetById.get(connection.to)!;
        const [fx, , fz] = from.position;
        const [tx, , tz] = to.position;
        if (connection.kind === 'support') {
            const lane = -1.2 - index * 0.28;
            return [
                new Vector3(fx, 0.24, fz - 0.2),
                new Vector3(fx, 0.24, lane),
                new Vector3(tx, 0.24, lane),
                new Vector3(tx, 0.24, tz - 0.2),
            ];
        }
        if (connection.kind === 'residential') {
            return [
                new Vector3(fx, 0.13, fz + 0.6),
                new Vector3(fx, 0.13, tz),
                new Vector3(tx, 0.13, tz),
            ];
        }
        if (connection.from === 'GRID')
            return [new Vector3(0, 2.9, fz), new Vector3(0, 1.95, tz - 0.2)];
        const height = 0.16;
        const midZ = connection.from === 'TR1' ? -4.9 : (fz + tz) / 2;
        return [
            new Vector3(fx, height, fz),
            new Vector3(fx, height, midZ),
            new Vector3(tx, height, midZ),
            new Vector3(tx, height, tz),
        ];
    }
    let supportIndex = 0;
    for (const connection of networkConnections) {
        const points = route(
            connection,
            connection.normallyOpen ? supportIndex++ : 0,
        );
        if (connection.normallyOpen) {
            const geometry = new BufferGeometry().setFromPoints(points);
            models.geometries.add(geometry);
            const line = new Line(geometry, support);
            line.computeLineDistances();
            supportGroup.add(line);
            continue;
        }
        const curve = new CurvePath<Vector3>();
        for (let index = 1; index < points.length; index++) {
            if (points[index - 1].distanceTo(points[index]) > 0.001)
                curve.add(new LineCurve3(points[index - 1], points[index]));
        }
        const material =
            connection.kind === 'solar'
                ? solar
                : connection.kind === 'residential'
                  ? residential
                  : supply;
        const geometry = new TubeGeometry(
            curve,
            Math.max(4, points.length * 3),
            connection.kind === 'residential' ? 0.018 : 0.037,
            5,
            false,
        );
        models.geometries.add(geometry);
        const tube = new Mesh(geometry, material);
        scene.add(tube);
        if (connection.kind !== 'residential') {
            const arrow = new Mesh(arrowGeometry, material);
            arrow.position.copy(curve.getPointAt(0.63));
            arrow.quaternion.setFromUnitVectors(
                arrow.up,
                curve.getTangentAt(0.63).normalize(),
            );
            scene.add(arrow);
        }
    }
    const selection = new Box3Helper(new Box3(), 0xd1bc85);
    selection.visible = false;
    scene.add(selection);
    models.geometries.add(selection.geometry);
    const selectionMaterial = selection.material as LineBasicMaterial;
    models.materials.add(selectionMaterial);
    const raycaster = new Raycaster();
    const pointer = new Vector2();
    let pointerStart: { x: number; y: number } | null = null;
    let disposed = false;
    let contextAvailable = true;
    let frame = 0;
    let width = 1;
    let height = 1;
    const labelHeights = {
        grid: 3.5,
        transformer: 2.55,
        solar: 1.4,
        bus: 0.85,
        panel: 2.25,
        home: 1.65,
    };

    function render(): void {
        if (disposed || !contextAvailable || frame) return;
        frame = requestAnimationFrame(() => {
            frame = 0;
            if (disposed || !contextAvailable) return;
            renderer.render(scene, camera);
            options.onProject(
                networkAssets.map((asset) => {
                    const point = new Vector3(...asset.position);
                    point.y += labelHeights[asset.kind];
                    point.project(camera);
                    return {
                        id: asset.id,
                        x: ((point.x + 1) * width) / 2,
                        y: ((1 - point.y) * height) / 2,
                        visible:
                            point.z > -1 &&
                            point.z < 1 &&
                            Math.abs(point.x) < 0.98 &&
                            Math.abs(point.y) < 0.98,
                    };
                }),
            );
        });
    }
    controls.addEventListener('change', render);

    function select(id: string): void {
        const root = roots.get(id);
        if (!root) return;
        root.updateWorldMatrix(true, true);
        selection.box.setFromObject(root).expandByScalar(0.1);
        selection.visible = true;
        render();
    }
    function setView(view: PlanView): void {
        controls.target.set(0, 0, -1.5);
        controls.cursor.copy(controls.target);
        const fit = Math.max(1, 1.3 / camera.aspect);
        const positions: Record<PlanView, Position> = {
            perspective: [22 * fit, 25 * fit, 31 * fit - 1.5],
            top: [0, 42 * fit, -1.4],
            front: [0, 15 * fit, 39 * fit - 1.5],
        };
        camera.position.set(...positions[view]);
        controls.update();
        render();
    }
    function zoom(factor: number): void {
        const offset = camera.position.clone().sub(controls.target);
        const distance = Math.min(
            controls.maxDistance,
            Math.max(controls.minDistance, offset.length() * factor),
        );
        camera.position.copy(controls.target).add(offset.setLength(distance));
        controls.update();
        render();
    }
    function focus(id: string): void {
        const root = roots.get(id);
        if (!root) return;
        const offset = camera.position
            .clone()
            .sub(controls.target)
            .setLength(assetById.get(id)?.kind === 'solar' ? 12 : 8);
        controls.target.copy(root.position).add(new Vector3(0, 0.6, 0));
        controls.cursor.copy(controls.target);
        camera.position.copy(controls.target).add(offset);
        controls.update();
        select(id);
    }
    function pick(event: PointerEvent): string | undefined {
        const rect = renderer.domElement.getBoundingClientRect();
        pointer.set(
            ((event.clientX - rect.left) / rect.width) * 2 - 1,
            (-(event.clientY - rect.top) / rect.height) * 2 + 1,
        );
        raycaster.setFromCamera(pointer, camera);
        const hit = raycaster.intersectObjects(pickable, true)[0];
        let object: Object3D | null = hit?.object ?? null;
        while (object) {
            if (typeof object.userData.assetId === 'string')
                return object.userData.assetId;
            object = object.parent;
        }
    }
    function pointerDown(event: PointerEvent): void {
        if (event.isPrimary && event.button === 0)
            pointerStart = { x: event.clientX, y: event.clientY };
        else pointerStart = null;
    }
    function pointerUp(event: PointerEvent): void {
        if (!pointerStart || !event.isPrimary || event.button !== 0) return;
        const distance = Math.hypot(
            event.clientX - pointerStart.x,
            event.clientY - pointerStart.y,
        );
        pointerStart = null;
        if (distance > 5) return;
        const id = pick(event);
        if (id) {
            select(id);
            options.onSelect(id);
        }
    }
    function pointerCancel(): void {
        pointerStart = null;
    }
    function contextLost(event: Event): void {
        event.preventDefault();
        contextAvailable = false;
    }
    function contextRestored(): void {
        contextAvailable = true;
        render();
    }
    renderer.domElement.addEventListener('pointerdown', pointerDown);
    renderer.domElement.addEventListener('pointerup', pointerUp);
    renderer.domElement.addEventListener('pointercancel', pointerCancel);
    renderer.domElement.addEventListener('webglcontextlost', contextLost);
    renderer.domElement.addEventListener(
        'webglcontextrestored',
        contextRestored,
    );

    function refreshTheme(): void {
        const dark = document.documentElement.classList.contains('dark');
        models.refreshTheme(dark);
        const gridMaterials = Array.isArray(grid.material)
            ? grid.material
            : [grid.material];
        gridMaterials.forEach((material) => {
            material.transparent = true;
            material.opacity = dark ? 0.22 : 0.16;
        });
        supply.color.set(dark ? 0x6eaebc : 0x397a91);
        solar.color.set(dark ? 0xc8a65b : 0x9c762d);
        residential.color.set(dark ? 0x648e86 : 0x507f73);
        selectionMaterial.color.copy(new Color(dark ? 0xdec78d : 0x9e6e22));
        render();
    }
    function resize(): void {
        if (disposed) return;
        const rect = host.getBoundingClientRect();
        if (!rect.width || !rect.height) return;
        const previousAspect = camera.aspect;
        width = rect.width;
        height = rect.height;
        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        const previousFit = Math.max(1, 1.3 / previousAspect);
        const nextFit = Math.max(1, 1.3 / camera.aspect);
        if (Math.abs(previousFit - nextFit) > 0.01) {
            const offset = camera.position.clone().sub(controls.target);
            const distance = Math.min(
                controls.maxDistance,
                Math.max(
                    controls.minDistance,
                    (offset.length() * nextFit) / previousFit,
                ),
            );
            camera.position
                .copy(controls.target)
                .add(offset.setLength(distance));
            controls.update();
        }
        render();
    }
    refreshTheme();
    resize();
    setView('perspective');
    select('TR1');

    return {
        resize,
        refreshTheme,
        setView,
        zoom,
        select,
        focus,
        showSupport(visible): void {
            supportGroup.visible = visible;
            render();
        },
        handleKey(event): void {
            if (event.key === 'Home' || event.key === 'Escape')
                setView('perspective');
            else if (event.key === '+' || event.key === '=') zoom(0.85);
            else if (event.key === '-') zoom(1.18);
            else if (
                ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(
                    event.key,
                )
            ) {
                const offset = camera.position.clone().sub(controls.target);
                const angle =
                    event.key === 'ArrowLeft'
                        ? -0.14
                        : event.key === 'ArrowRight'
                          ? 0.14
                          : 0;
                if (angle) offset.applyAxisAngle(new Vector3(0, 1, 0), angle);
                else offset.y += event.key === 'ArrowUp' ? 1.5 : -1.5;
                camera.position.copy(controls.target).add(offset);
                controls.update();
                render();
            } else return;
            event.preventDefault();
        },
        dispose(): void {
            disposed = true;
            cancelAnimationFrame(frame);
            controls.removeEventListener('change', render);
            controls.dispose();
            renderer.domElement.removeEventListener('pointerdown', pointerDown);
            renderer.domElement.removeEventListener('pointerup', pointerUp);
            renderer.domElement.removeEventListener(
                'pointercancel',
                pointerCancel,
            );
            renderer.domElement.removeEventListener(
                'webglcontextlost',
                contextLost,
            );
            renderer.domElement.removeEventListener(
                'webglcontextrestored',
                contextRestored,
            );
            models.geometries.forEach((geometry) => geometry.dispose());
            models.materials.forEach((material: Material) =>
                material.dispose(),
            );
            grid.geometry.dispose();
            (Array.isArray(grid.material)
                ? grid.material
                : [grid.material]
            ).forEach((material) => material.dispose());
            renderer.dispose();
            renderer.forceContextLoss();
            renderer.domElement.remove();
        },
    };
}
