def get_three_js_string(layers_config):
    import json
    js_layers = json.dumps(layers_config)

    three_js_code = f"""
    <div id="container" style="width: 100%; height: 700px;"></div>
    <script type="importmap">
    {{
        "imports": {{
        "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
        "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
        }}
    }}
    </script>

    <script type="module">
        import * as THREE from 'three';
        import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';

        const layersData = {js_layers};
        const container = document.getElementById('container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xffffff);

        const camera = new THREE.PerspectiveCamera(75, container.clientWidth / 500, 0.1, 1000);
        camera.position.set(10, 15, 10);

        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(container.clientWidth, 500);
        container.appendChild(renderer.domElement);
        // HELPER: Create procedural patterns
        function createPatternTexture(type) {{
            const canvas = document.createElement('canvas');
            canvas.width = 256;
            canvas.height = 256;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = 'white'; 
            ctx.fillRect(0, 0, 256, 256);
            ctx.strokeStyle = 'black';
            

            if (type === 'braid') {{
                ctx.lineWidth = 5;
                // Interweaving braid lines (cross-hatch pattern)
                ctx.beginPath();
                for (let i = -256; i < 256; i += 32) {{
                    ctx.moveTo(i, 0);
                    ctx.lineTo(i + 256, 256);
                    ctx.moveTo(i + 256, 0);
                    ctx.lineTo(i, 256);
                }}
                ctx.stroke();
            }} else if (type === 'spiral-coil') {{
                ctx.lineWidth = 8;
                // Draw diagonal lines for the spiral
                ctx.beginPath();
                ctx.moveTo(0, 0); ctx.lineTo(256, 256);
                ctx.moveTo(-256, 0); ctx.lineTo(0, 256);
                ctx.moveTo(256, 0); ctx.lineTo(512, 256);
                ctx.stroke();
            }}
            const texture = new THREE.CanvasTexture(canvas);
            texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
            if (type === 'spiral-coil') {{
                // Increase the second number to make the coil tighter along the length
                texture.repeat.set(1, 5); 
            }} else {{
                // Keep the original repeat for the braid pattern[cite: 1]
                texture.repeat.set(4, 1);
            }}

            //texture.repeat.set(4, 1); // Repeat the pattern around the cylinder
            return texture;
        }}
        const baseLength = 10;
        const step = 1.2;

        // Create Layers
        layersData.forEach((layer, index) => {{
            // 1. Calculate length. 
            // If it's the last layer (FEP), we make it significantly longer.
            const isLast = index === layersData.length - 1;
            const backExtension = isLast ? 5 : 0; 
            const length = (baseLength - (index * step)) + backExtension;

            const geometry = new THREE.CylinderGeometry(layer.radius, layer.radius, length, 64);
            
            const material = new THREE.MeshPhongMaterial({{ 
                color: layer.color,
                shininess: 80,
                // Adding a slight transparency/opacity or different specular 
                // can also help distinguish layers
                specular: 0x222222 
            }});
            
            // Apply patterns based on index
            if (index === 2) {{ // 3rd Cylinder (Braid Wire)
                material.map = createPatternTexture('braid');
            }} else if (index === 3) {{ // 4th Cylinder (Coil Wire)
                material.map = createPatternTexture('spiral-coil');
            }}

            const mesh = new THREE.Mesh(geometry, material);
            mesh.rotation.x = Math.PI / 2;

            // 2. Position logic:
            // We want the 'front' face (positive Z) to stay staggered.
            // In Three.js, Cylinder center is 0. 
            // Front face position = mesh.position.z + (length / 2)
            // We set front face to: (baseLength / 2) - (index * step)
            mesh.position.z = ((baseLength / 2) - (index * step)) - (length / 2);

            scene.add(mesh);
        }});

        // Lighting
        const light1 = new THREE.DirectionalLight(0xffffff, 2);
        light1.position.set(10, 10, 10);
        scene.add(light1);
        
        const light2 = new THREE.DirectionalLight(0xffffff, 1);
        light2.position.set(-10, -10, -10);
        scene.add(light2);

        scene.add(new THREE.AmbientLight(0xffffff, 0.6));

        const controls = new OrbitControls(camera, renderer.domElement);
        controls.target.set(0, -7, 0); // This sets the "pivot point" to the new height
        controls.update();
        controls.enableDamping = true;

        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();

        window.addEventListener('resize', () => {{
            camera.aspect = container.clientWidth / 500;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, 500);
        }});
    </script>
    """
    return three_js_code