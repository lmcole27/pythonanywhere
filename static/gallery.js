const galleryImages = document.querySelectorAll('.gallery-item img');

if (galleryImages.length) {
    const viewer = document.createElement('dialog');
    viewer.className = 'gallery-viewer';
    viewer.setAttribute('aria-label', 'Enlarged gallery image');

    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.className = 'gallery-viewer-close';
    closeButton.textContent = '×';
    closeButton.setAttribute('aria-label', 'Close');

    const enlargedImage = document.createElement('img');
    viewer.append(closeButton, enlargedImage);
    document.body.append(viewer);

    closeButton.addEventListener('click', () => viewer.close());
    viewer.addEventListener('click', (event) => {
        if (event.target === viewer) viewer.close();
    });
    viewer.addEventListener('close', () => {
        document.body.classList.remove('gallery-viewer-open');
    });

    galleryImages.forEach((image) => {
        const trigger = document.createElement('button');
        trigger.type = 'button';
        trigger.className = 'gallery-image-trigger';
        trigger.setAttribute('aria-label', `Enlarge ${image.alt}`);
        image.before(trigger);
        trigger.append(image);
        trigger.addEventListener('click', () => {
            enlargedImage.src = image.currentSrc || image.src;
            enlargedImage.alt = image.alt;
            viewer.showModal();
            document.body.classList.add('gallery-viewer-open');
        });
    });
}
