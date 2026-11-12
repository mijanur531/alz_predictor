/**
 * 3D Realistic Hospital Campus & Doctor Hologram (Three.js)
 * Renders an interactive 3D medical center tower with glowing architectural windows,
 * medical cross, emergency wing, landscaped plaza, trees, and an animated 3D Doctor.
 */

document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('hospital3DContainer') || document.querySelector('.doctor-avatar-3d-container');
    if (!container || typeof THREE === 'undefined') return;

    // 1. Scene, Camera, Renderer Setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0f172a); // Deep medical navy slate
    scene.fog = new THREE.FogExp2(0x0f172a, 0.035);

    const width = container.clientWidth || 400;
    const height = container.clientHeight || 280;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 4, 12);
    camera.lookAt(0, 1.5, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // Clear old canvases
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // 2. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xe0f2fe, 1.2);
    sunLight.position.set(10, 20, 10);
    sunLight.castShadow = true;
    scene.add(sunLight);

    const blueGlowLight = new THREE.PointLight(0x0284c7, 2.5, 20);
    blueGlowLight.position.set(0, 6, 2);
    scene.add(blueGlowLight);

    const cyanAccentLight = new THREE.PointLight(0x06b6d4, 1.5, 15);
    cyanAccentLight.position.set(-4, 2, 4);
    scene.add(cyanAccentLight);

    // 3. Hospital Ground & Landscaped Plaza
    const groundGeo = new THREE.PlaneGeometry(30, 30);
    const groundMat = new THREE.MeshLambertMaterial({ color: 0x1e293b });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.5;
    ground.receiveShadow = true;
    scene.add(ground);

    // Green lawn patch
    const lawnGeo = new THREE.BoxGeometry(14, 0.1, 8);
    const lawnMat = new THREE.MeshLambertMaterial({ color: 0x065f46 });
    const lawn = new THREE.Mesh(lawnGeo, lawnMat);
    lawn.position.set(0, -0.45, 1);
    scene.add(lawn);

    // 4. Main Hospital Building Complex
    const hospitalGroup = new THREE.Group();
    hospitalGroup.position.set(-1.5, 0, -2);
    scene.add(hospitalGroup);

    // Main Central Tower (Glass & Steel)
    const towerGeo = new THREE.BoxGeometry(5.5, 7.5, 3.5);
    const towerMat = new THREE.MeshLambertMaterial({ color: 0x334155 });
    const mainTower = new THREE.Mesh(towerGeo, towerMat);
    mainTower.position.y = 3.25;
    mainTower.castShadow = true;
    hospitalGroup.add(mainTower);

    // Tower Glass Curtain Windows (Glowing Cyan)
    const windowGeo = new THREE.BoxGeometry(5.2, 6.8, 3.6);
    const windowMat = new THREE.MeshLambertMaterial({ 
        color: 0x38bdf8,
        emissive: 0x0284c7,
        emissiveIntensity: 0.35,
        transparent: true,
        opacity: 0.85
    });
    const towerWindows = new THREE.Mesh(windowGeo, windowMat);
    towerWindows.position.y = 3.25;
    hospitalGroup.add(towerWindows);

    // Emergency & Diagnostics Wing (Right Wing)
    const wingGeo = new THREE.BoxGeometry(4, 4, 3);
    const wingMat = new THREE.MeshLambertMaterial({ color: 0x1e293b });
    const rightWing = new THREE.Mesh(wingGeo, wingMat);
    rightWing.position.set(4, 1.5, 0.5);
    rightWing.castShadow = true;
    hospitalGroup.add(rightWing);

    // Wing Glass Front
    const wingGlassGeo = new THREE.BoxGeometry(3.8, 3.5, 3.1);
    const wingGlassMat = new THREE.MeshLambertMaterial({
        color: 0x06b6d4,
        emissive: 0x0891b2,
        emissiveIntensity: 0.3,
        transparent: true,
        opacity: 0.8
    });
    const wingGlass = new THREE.Mesh(wingGlassGeo, wingGlassMat);
    wingGlass.position.set(4, 1.5, 0.5);
    hospitalGroup.add(wingGlass);

    // Medical Red/Cyan Cross on Roof
    const crossMat = new THREE.MeshBasicMaterial({ color: 0xef4444 });
    const crossV = new THREE.Mesh(new THREE.BoxGeometry(0.3, 1.2, 0.2), crossMat);
    crossV.position.set(0, 7.3, 1.8);
    hospitalGroup.add(crossV);

    const crossH = new THREE.Mesh(new THREE.BoxGeometry(1.0, 0.35, 0.2), crossMat);
    crossH.position.set(0, 7.3, 1.8);
    hospitalGroup.add(crossH);

    // Helipad on Roof
    const helipadGeo = new THREE.CylinderGeometry(1.2, 1.2, 0.1, 24);
    const helipadMat = new THREE.MeshLambertMaterial({ color: 0x475569 });
    const helipad = new THREE.Mesh(helipadGeo, helipadMat);
    helipad.position.set(4, 3.55, 0.5);
    hospitalGroup.add(helipad);

    // 5. Landscaping - Trees (Cone + Trunk)
    function createTree(x, z) {
        const treeGroup = new THREE.Group();
        const trunkGeo = new THREE.CylinderGeometry(0.1, 0.15, 0.8, 8);
        const trunkMat = new THREE.MeshLambertMaterial({ color: 0x78350f });
        const trunk = new THREE.Mesh(trunkGeo, trunkMat);
        trunk.position.y = 0.4;
        treeGroup.add(trunk);

        const foliageGeo = new THREE.ConeGeometry(0.6, 1.4, 8);
        const foliageMat = new THREE.MeshLambertMaterial({ color: 0x10b981 });
        const foliage = new THREE.Mesh(foliageGeo, foliageMat);
        foliage.position.y = 1.3;
        treeGroup.add(foliage);

        treeGroup.position.set(x, -0.45, z);
        scene.add(treeGroup);
    }

    createTree(-4.5, 2.5);
    createTree(-5.5, 1.0);
    createTree(4.5, 3.5);
    createTree(5.5, 2.0);

    // 6. Interactive 3D Doctor Hologram Avatar in Courtyard
    const doctorGroup = new THREE.Group();
    doctorGroup.position.set(2.2, 0, 3.5);
    scene.add(doctorGroup);

    // Doctor Body (White Lab Coat)
    const bodyGeo = new THREE.ConeGeometry(0.7, 1.8, 16);
    const bodyMat = new THREE.MeshLambertMaterial({ color: 0xffffff });
    const doctorBody = new THREE.Mesh(bodyGeo, bodyMat);
    doctorBody.position.y = 0.9;
    doctorGroup.add(doctorBody);

    // Doctor Head (Skin Sphere)
    const headGeo = new THREE.SphereGeometry(0.38, 24, 24);
    const headMat = new THREE.MeshLambertMaterial({ color: 0xfbbf24 });
    const doctorHead = new THREE.Mesh(headGeo, headMat);
    doctorHead.position.y = 2.0;
    doctorGroup.add(doctorHead);

    // Doctor Hair (Dark Box)
    const hairGeo = new THREE.BoxGeometry(0.78, 0.2, 0.78);
    const hairMat = new THREE.MeshLambertMaterial({ color: 0x1e293b });
    const doctorHair = new THREE.Mesh(hairGeo, hairMat);
    doctorHair.position.y = 2.3;
    doctorGroup.add(doctorHair);

    // Stethoscope / Blue Tie
    const tieGeo = new THREE.BoxGeometry(0.12, 0.6, 0.05);
    const tieMat = new THREE.MeshLambertMaterial({ color: 0x0284c7 });
    const doctorTie = new THREE.Mesh(tieGeo, tieMat);
    doctorTie.position.set(0, 1.4, 0.45);
    doctorGroup.add(doctorTie);

    // 7. Interactive Floating Hologram Rings around Doctor
    const ringGeo = new THREE.RingGeometry(0.8, 0.9, 32);
    const ringMat = new THREE.MeshBasicMaterial({
        color: 0x38bdf8,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.7
    });
    const holoRing = new THREE.Mesh(ringGeo, ringMat);
    holoRing.rotation.x = Math.PI / 2;
    holoRing.position.set(2.2, 0.05, 3.5);
    scene.add(holoRing);

    // 8. Mouse Movement & Parallax Orbit
    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    container.addEventListener('mousemove', function(e) {
        const rect = container.getBoundingClientRect();
        mouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        mouseY = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
    });

    // Touch support for mobile devices
    container.addEventListener('touchmove', function(e) {
        if (e.touches.length > 0) {
            const rect = container.getBoundingClientRect();
            mouseX = ((e.touches[0].clientX - rect.left) / rect.width) * 2 - 1;
            mouseY = -(((e.touches[0].clientY - rect.top) / rect.height) * 2 - 1);
        }
    }, { passive: true });

    // 9. Animation Loop
    const clock = new THREE.Clock();
    let isSpeaking = false;

    function animate() {
        requestAnimationFrame(animate);
        const elapsedTime = clock.getElapsedTime();

        // Parallax camera lerping
        targetX = mouseX * 2.5;
        targetY = 4 + mouseY * 1.2;
        camera.position.x += (targetX - camera.position.x) * 0.05;
        camera.position.y += (targetY - camera.position.y) * 0.05;
        camera.lookAt(0, 1.8, 0);

        // Doctor head bobbing and breathing
        doctorHead.rotation.y = Math.sin(elapsedTime * 1.5) * 0.15 + (mouseX * 0.25);
        doctorHead.position.y = 2.0 + Math.sin(elapsedTime * 2.0) * 0.03;
        doctorBody.position.y = 0.9 + Math.sin(elapsedTime * 1.5) * 0.015;

        // Animate speaking motion if active
        if (isSpeaking) {
            doctorHead.position.y = 2.0 + Math.sin(elapsedTime * 14.0) * 0.04;
        }

        // Hologram ring pulsing and rotation
        holoRing.rotation.z += 0.015;
        holoRing.scale.setScalar(1 + Math.sin(elapsedTime * 3.0) * 0.06);

        // Gentle light pulsing
        blueGlowLight.intensity = 2.2 + Math.sin(elapsedTime * 2.5) * 0.5;

        renderer.render(scene, camera);
    }
    animate();

    // 10. Voice Speech Synthesis Trigger for Doctor Alex / Evelyn
    const btnSpeak = document.getElementById('btnSpeakDoctorAdvice');
    const btnStop = document.getElementById('btnStopDoctorSpeech');
    const speechBubble = document.getElementById('doctorSpeechBubble');
    const speakingBadge = document.getElementById('doctorSpeakingBadge');

    const doctorSpeechText = "Welcome to AlzPredictor Medical Center. I am Dr. Evelyn. Our platform offers multi-factor AI risk assessment, interactive 3D VR memory tasks, and verified neurologist consultation. Take a quick cognitive screening today.";

    if (btnSpeak && 'speechSynthesis' in window) {
        btnSpeak.addEventListener('click', function() {
            window.speechSynthesis.cancel(); // Stop any active utterance
            
            const utterance = new SpeechSynthesisUtterance(doctorSpeechText);
            utterance.rate = 0.95;
            utterance.pitch = 1.05;

            // Pick English voice if available
            const voices = window.speechSynthesis.getVoices();
            const preferredVoice = voices.find(v => v.lang.includes('en') && (v.name.includes('Female') || v.name.includes('Google') || v.name.includes('Natural')));
            if (preferredVoice) utterance.voice = preferredVoice;

            utterance.onstart = function() {
                isSpeaking = true;
                if (speakingBadge) speakingBadge.classList.remove('d-none');
                if (speechBubble) speechBubble.classList.add('border-primary', 'shadow-sm');
            };

            utterance.onend = function() {
                isSpeaking = false;
                if (speakingBadge) speakingBadge.classList.add('d-none');
                if (speechBubble) speechBubble.classList.remove('border-primary', 'shadow-sm');
            };

            utterance.onerror = function() {
                isSpeaking = false;
                if (speakingBadge) speakingBadge.classList.add('d-none');
            };

            window.speechSynthesis.speak(utterance);
        });
    }

    if (btnStop && 'speechSynthesis' in window) {
        btnStop.addEventListener('click', function() {
            window.speechSynthesis.cancel();
            isSpeaking = false;
            if (speakingBadge) speakingBadge.classList.add('d-none');
        });
    }

    // Responsive window resize
    window.addEventListener('resize', function() {
        const newW = container.clientWidth || 400;
        const newH = container.clientHeight || 280;
        camera.aspect = newW / newH;
        camera.updateProjectionMatrix();
        renderer.setSize(newW, newH);
    });
});
