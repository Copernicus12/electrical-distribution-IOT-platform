import {
    BoxGeometry,
    BufferGeometry,
    ConeGeometry,
    CylinderGeometry,
    Float32BufferAttribute,
    Group,
    Mesh,
    MeshStandardMaterial,
    SphereGeometry,
} from 'three';
import type { Material } from 'three';
import type { AssetKind, NetworkAsset, Position } from './networkTopology';

export function createNetworkModels() {
    const geometries = new Set<BufferGeometry>();
    const materials = new Set<Material>();
    function geometry<T extends BufferGeometry>(value: T): T {
        geometries.add(value);
        return value;
    }
    function material(color: number, metalness = 0.2, roughness = 0.7) {
        const value = new MeshStandardMaterial({ color, metalness, roughness });
        materials.add(value);
        return value;
    }
    const surfaces = {
        platform: material(0x202326),
        district: material(0x292d30),
        road: material(0x171a1c),
        metal: material(0x858f96, 0.6, 0.4),
        trim: material(0x485158, 0.55),
        dark: material(0x1b2228),
        wall: material(0xb2b9b9, 0.05),
        roof: material(0x3e4d58, 0.4),
        glass: material(0x6ca5b7, 0.5, 0.25),
        solar: material(0x1a3c58, 0.5, 0.25),
        ceramic: material(0x9c9081, 0.1),
        copper: material(0xaa7953, 0.6),
        green: material(0x506a60, 0.05),
        amber: material(0xd2a85b),
    };
    surfaces.glass.emissive.set(0x264955);
    surfaces.glass.emissiveIntensity = 0.2;
    const cube = geometry(new BoxGeometry(1, 1, 1));
    const cylinder = geometry(new CylinderGeometry(1, 1, 1, 12));
    const sphere = geometry(new SphereGeometry(1, 8, 6));
    const treeCrown = geometry(new ConeGeometry(0.35, 0.9, 7));
    const roof = geometry(new BufferGeometry());
    roof.setAttribute(
        'position',
        new Float32BufferAttribute(
            [
                -0.78, 0, -0.66, 0.78, 0, -0.66, 0, 0.43, -0.66, -0.78, 0, 0.66,
                0.78, 0, 0.66, 0, 0.43, 0.66,
            ],
            3,
        ),
    );
    roof.setIndex([
        0, 2, 1, 3, 4, 5, 0, 3, 5, 0, 5, 2, 1, 2, 5, 1, 5, 4, 0, 1, 4, 0, 4, 3,
    ]);
    roof.computeVertexNormals();

    function box(
        parent: Group,
        size: Position,
        position: Position,
        surface = surfaces.metal,
    ) {
        const mesh = new Mesh(cube, surface);
        mesh.scale.set(...size);
        mesh.position.set(...position);
        parent.add(mesh);
        return mesh;
    }
    function round(
        parent: Group,
        size: Position,
        position: Position,
        surface = surfaces.trim,
    ) {
        const mesh = new Mesh(cylinder, surface);
        mesh.scale.set(...size);
        mesh.position.set(...position);
        parent.add(mesh);
        return mesh;
    }
    function beam(parent: Group, from: Position, to: Position, radius = 0.035) {
        const mesh = round(parent, [radius, 1, radius], from);
        const end = mesh.position.clone().set(...to);
        const direction = end.sub(mesh.position);
        mesh.scale.y = direction.length();
        mesh.position.addScaledVector(direction, 0.5);
        mesh.quaternion.setFromUnitVectors(mesh.up, direction.normalize());
    }
    function panel(root: Group) {
        box(root, [1.1, 0.14, 0.85], [0, 0.12, 0], surfaces.trim);
        box(root, [0.96, 1.72, 0.62], [0, 1.04, 0], surfaces.metal);
        box(root, [0.83, 1.5, 0.025], [0, 1.04, 0.325], surfaces.dark);
        for (let row = 0; row < 6; row++) {
            box(root, [0.72, 0.02, 0.03], [0, 0.45 + row * 0.19, 0.35]);
            for (let col = 0; col < 7; col++) {
                box(
                    root,
                    [0.072, 0.1, 0.09],
                    [-0.31 + col * 0.1, 0.5 + row * 0.19, 0.38],
                    surfaces.wall,
                );
            }
        }
        box(root, [0.29, 0.2, 0.09], [-0.18, 1.64, 0.38], surfaces.dark);
        box(root, [0.2, 0.09, 0.01], [-0.18, 1.67, 0.43], surfaces.glass);
        const door = new Group();
        door.position.set(-0.49, 1.04, 0.34);
        door.rotation.y = -0.85;
        root.add(door);
        box(door, [0.91, 1.64, 0.035], [0.455, 0, 0]);
        box(door, [0.025, 0.27, 0.045], [0.8, -0.05, 0.04], surfaces.dark);
        for (let row = 0; row < 3; row++) {
            box(
                door,
                [0.63, 0.02, 0.008],
                [0.43, 0.31 - row * 0.25, 0.023],
                surfaces.dark,
            );
            for (const x of [0.25, 0.62]) {
                box(
                    door,
                    [0.1, 0.11, 0.05],
                    [x, 0.26 - row * 0.25, 0.045],
                    surfaces.dark,
                );
            }
        }
        box(door, [0.22, 0.16, 0.03], [0.3, 0.62, 0.04], surfaces.dark);
        box(door, [0.16, 0.08, 0.01], [0.3, 0.64, 0.06], surfaces.glass);
    }
    function transformer(root: Group) {
        box(root, [3, 0.15, 2.3], [0, 0.12, 0], surfaces.district);
        box(root, [1.95, 1.23, 1.3], [0, 0.9, 0]);
        box(root, [2.08, 0.12, 1.45], [0, 1.55, 0], surfaces.trim);
        for (let i = 0; i < 13; i++) {
            for (const z of [-0.81, 0.81]) {
                box(
                    root,
                    [0.055, 0.95, 0.32],
                    [-0.84 + i * 0.14, 0.89, z],
                    surfaces.trim,
                );
            }
        }
        for (const x of [-0.62, 0, 0.62]) {
            round(root, [0.06, 0.5, 0.06], [x, 1.8, -0.2], surfaces.copper);
            for (let ring = 0; ring < 5; ring++) {
                round(
                    root,
                    [0.14, 0.055, 0.14],
                    [x, 1.65 + ring * 0.08, -0.2],
                    surfaces.ceramic,
                );
            }
            round(root, [0.075, 0.27, 0.075], [x, 1.73, 0.4], surfaces.dark);
        }
        round(root, [0.23, 1.55, 0.23], [0, 1.84, -0.56]).rotation.z =
            Math.PI / 2;
        box(root, [0.45, 0.28, 0.03], [0, 1.06, 0.67], surfaces.dark);
        box(root, [0.23, 0.17, 0.015], [0, 1.06, 0.69], surfaces.amber);
        for (const x of [-0.7, 0.7])
            box(root, [0.22, 0.12, 1.7], [x, 0.24, 0], surfaces.dark);
    }
    function grid(root: Group) {
        box(root, [2.4, 0.12, 1.25], [0, 0.1, 0], surfaces.district);
        for (const x of [-0.8, 0.8]) {
            beam(root, [x, 0.15, 0], [x * 0.5, 3, 0]);
            for (let i = 0; i < 3; i++) {
                const low = 0.35 + i * 0.82;
                beam(
                    root,
                    [-0.75 + i * 0.1, low, 0],
                    [0.65 - i * 0.1, low + 0.8, 0],
                    0.018,
                );
                beam(
                    root,
                    [0.75 - i * 0.1, low, 0],
                    [-0.65 + i * 0.1, low + 0.8, 0],
                    0.018,
                );
            }
        }
        box(root, [3.1, 0.09, 0.13], [0, 2.7, 0]);
        for (const x of [-1.25, 0, 1.25]) {
            for (let i = 0; i < 4; i++)
                round(
                    root,
                    [0.1, 0.05, 0.1],
                    [x, 2.78 + i * 0.07, 0],
                    surfaces.ceramic,
                );
        }
    }
    function solar(root: Group) {
        box(root, [4.8, 0.08, 3.2], [0, 0.1, 0], surfaces.district);
        for (let row = 0; row < 2; row++) {
            for (let col = 0; col < 3; col++) {
                const rack = new Group();
                rack.position.set(-1.5 + col * 1.5, 0.65, -0.75 + row * 1.5);
                root.add(rack);
                for (const x of [-0.5, 0.5])
                    box(rack, [0.035, 0.5, 0.035], [x, -0.25, 0]);
                const module = new Group();
                module.rotation.x = 0.3;
                rack.add(module);
                box(module, [1.4, 0.06, 1.3], [0, 0, 0], surfaces.metal);
                box(module, [1.32, 0.012, 1.22], [0, 0.038, 0], surfaces.solar);
                for (let cell = 1; cell < 6; cell++)
                    box(
                        module,
                        [0.008, 0.005, 1.22],
                        [-0.66 + cell * 0.22, 0.047, 0],
                        surfaces.trim,
                    );
                for (let cell = 1; cell < 4; cell++)
                    box(
                        module,
                        [1.32, 0.005, 0.008],
                        [0, 0.047, -0.61 + cell * 0.305],
                        surfaces.trim,
                    );
            }
        }
        box(root, [0.35, 0.6, 0.25], [2, 0.4, 1.1]);
    }
    function home(root: Group) {
        box(root, [1.68, 0.06, 1.55], [0, 0.1, 0], surfaces.district);
        box(root, [1.4, 0.8, 1.12], [0, 0.53, 0], surfaces.wall);
        const top = new Mesh(roof, surfaces.roof);
        top.position.y = 0.93;
        root.add(top);
        box(root, [0.2, 0.4, 0.2], [0.36, 1.18, -0.18], surfaces.trim);
        box(root, [0.25, 0.5, 0.03], [0.1, 0.38, 0.576], surfaces.dark);
        for (const x of [-0.44, 0.48]) {
            box(root, [0.29, 0.28, 0.025], [x, 0.59, 0.578], surfaces.glass);
            box(root, [0.015, 0.29, 0.012], [x, 0.59, 0.596], surfaces.trim);
        }
        for (const z of [-0.27, 0.27])
            box(root, [0.02, 0.26, 0.29], [0.71, 0.59, z], surfaces.glass);
    }
    function bus(root: Group) {
        box(root, [0.65, 0.18, 0.65], [0, 0.18, 0], surfaces.trim);
        box(root, [0.4, 0.25, 0.4], [0, 0.36, 0], surfaces.dark);
        box(root, [0.25, 0.035, 0.25], [0, 0.51, 0], surfaces.copper);
    }
    const builders: Record<AssetKind, (root: Group) => void> = {
        panel,
        transformer,
        grid,
        solar,
        home,
        bus,
    };

    return {
        geometries,
        materials,
        createAsset(asset: NetworkAsset): Group {
            const root = new Group();
            root.name = asset.id;
            root.userData.assetId = asset.id;
            root.position.set(...asset.position);
            builders[asset.kind](root);
            return root;
        },
        createSite(): Group {
            const root = new Group();
            box(root, [26, 0.18, 25], [0, -0.08, -1.5], surfaces.platform);
            box(root, [25.5, 0.015, 0.6], [0, 0.025, 1.7], surfaces.road);
            for (const x of [-9, -3, 3, 9]) {
                box(
                    root,
                    [5.35, 0.035, 7.7],
                    [x, 0.03, 5.85],
                    surfaces.district,
                );
                box(root, [0.34, 0.035, 7.6], [x, 0.06, 5.85], surfaces.road);
            }
            for (const x of [-12, 12]) {
                for (const z of [-8.5, -3.8, 1.7, 5.5, 9]) {
                    round(
                        root,
                        [0.045, 0.6, 0.045],
                        [x, 0.35, z],
                        surfaces.copper,
                    );
                    const crown = new Mesh(treeCrown, surfaces.green);
                    crown.position.set(x, 0.95, z);
                    root.add(crown);
                    const base = new Mesh(sphere, surfaces.green);
                    base.scale.set(0.25, 0.06, 0.25);
                    base.position.set(x, 0.08, z);
                    root.add(base);
                }
            }
            return root;
        },
        refreshTheme(dark: boolean): void {
            surfaces.platform.color.set(dark ? 0x1b1e21 : 0xe5e9ec);
            surfaces.district.color.set(dark ? 0x262c30 : 0xd6dfe3);
            surfaces.road.color.set(dark ? 0x111619 : 0xc1cbd0);
            surfaces.wall.color.set(dark ? 0x8c9a9d : 0xcbd1cd);
            surfaces.roof.color.set(dark ? 0x344955 : 0x526d7c);
        },
    };
}
