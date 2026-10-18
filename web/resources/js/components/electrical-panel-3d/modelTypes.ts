import type {
    BufferGeometry,
    CanvasTexture,
    Group,
    Material,
    Mesh,
    Vector3Tuple,
} from 'three';

export type PanelModelTools = {
    box: (
        parent: Group,
        size: Vector3Tuple,
        position: Vector3Tuple,
        material: Material,
    ) => Mesh;
    cable: (
        parent: Group,
        points: Vector3Tuple[],
        radius?: number,
        material?: Material,
    ) => void;
    geometries: Set<BufferGeometry>;
    materials: Set<Material>;
    textures: Set<CanvasTexture>;
};

export type PanelMaterials = {
    metal: Material;
    trim: Material;
    back: Material;
    terminal: Material;
    duct: Material;
    recess: Material;
    wire: Material;
    indicator: Material;
};
