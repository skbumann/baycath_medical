def get_three_js_string(layers_config):
    import json
    js_layers = json.dumps(layers_config)

    three_js_code = f"""
    <div id="container" style="width: 100%; height: 700px; position: relative;">
        <svg id="label-svg" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; overflow: visible;"></svg>
    </div>
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
        const labelAnchors = []; // {{ worldPos: Vector3, index: number }}
        const svg = document.getElementById('label-svg');
        const svgNS = 'http://www.w3.org/2000/svg';

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

            // Anchor: top edge of the open (front) face of the cylinder.
            // The mesh is rotated Math.PI/2 on X, so the cylinder's radial Y maps to world Y.
            // Front face is at mesh.position.z + length/2.
            const frontZ = mesh.position.z + (length / 2);
            const anchorWorld = new THREE.Vector3(0, layer.radius, frontZ);
            labelAnchors.push({{ worldPos: anchorWorld, name: layer.name, index }});
        }});

        // Build SVG elements for each label (line + elbow + rect + text)
        const svgEls = labelAnchors.map((anchor) => {{
            const line = document.createElementNS(svgNS, 'line');
            line.setAttribute('stroke', '#888');
            line.setAttribute('stroke-width', '1.5');

            const elbow = document.createElementNS(svgNS, 'line');
            elbow.setAttribute('stroke', '#888');
            elbow.setAttribute('stroke-width', '1.5');

            const dot = document.createElementNS(svgNS, 'circle');
            dot.setAttribute('r', '3');
            dot.setAttribute('fill', '#555');

            const rect = document.createElementNS(svgNS, 'rect');
            rect.setAttribute('rx', '4');
            rect.setAttribute('fill', 'rgba(255,255,255,0.9)');
            rect.setAttribute('stroke', '#bbb');
            rect.setAttribute('stroke-width', '1');

            const text = document.createElementNS(svgNS, 'text');
            text.textContent = anchor.name;
            text.setAttribute('font-family', 'sans-serif');
            text.setAttribute('font-size', '11');
            text.setAttribute('font-weight', '600');
            text.setAttribute('fill', '#222');
            text.setAttribute('dominant-baseline', 'middle');

            // Add in order: line behind, then rect, then text on top
            svg.appendChild(line);
            svg.appendChild(elbow);
            svg.appendChild(dot);
            svg.appendChild(rect);
            svg.appendChild(text);
            return {{ line, elbow, dot, rect, text }};
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

        function updateLabels() {{
            const w = container.clientWidth;
            const h = 500;
            const topPadding = 16; // px from top edge to label centre
            const labelSpacing = w / (labelAnchors.length + 1);

            labelAnchors.forEach((anchor, i) => {{
                const {{ line, elbow, dot, rect, text }} = svgEls[i];

                // Project world anchor to screen
                const pos = anchor.worldPos.clone().project(camera);
                const hidden = pos.z > 1;

                if (hidden) {{
                    [line, elbow, dot, rect, text].forEach(el => el.setAttribute('visibility', 'hidden'));
                    return;
                }}
                [line, elbow, dot, rect, text].forEach(el => el.setAttribute('visibility', 'visible'));

                const ax = (pos.x * 0.5 + 0.5) * w;
                const ay = (-pos.y * 0.5 + 0.5) * h;

                // Evenly spaced label X positions along the top
                const lx_center = labelSpacing * (i + 1);

                // Measure text to size the rect
                const bbox = text.getBBox ? text.getBBox() : {{ width: 80, height: 14 }};
                const rectPad = {{ x: 6, y: 4 }};
                const rw = bbox.width + rectPad.x * 2;
                const rh = bbox.height + rectPad.y * 2;

                const lx = lx_center - rw / 2; // left edge of label box, centred on slot
                const ly = topPadding;          // top edge of label box

                // Dot at the anchor point on the cylinder surface
                dot.setAttribute('cx', ax);
                dot.setAttribute('cy', ay);

                // Diagonal line from anchor up to just below the label
                const elbowY = ly + rh + 10;
                line.setAttribute('x1', ax);
                line.setAttribute('y1', ay);
                line.setAttribute('x2', lx_center);
                line.setAttribute('y2', elbowY);

                // Short vertical stub from elbow into bottom of label box
                elbow.setAttribute('x1', lx_center);
                elbow.setAttribute('y1', elbowY);
                elbow.setAttribute('x2', lx_center);
                elbow.setAttribute('y2', ly + rh);

                // Label rect
                rect.setAttribute('x', lx);
                rect.setAttribute('y', ly);
                rect.setAttribute('width', rw);
                rect.setAttribute('height', rh);

                // Label text centred in rect
                text.setAttribute('x', lx + rectPad.x);
                text.setAttribute('y', ly + rh / 2);
            }});
        }}

        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
            updateLabels();
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