odoo.define('hm_picture_library.external_image_zoom', function (require) {
    'use strict';

    var core = require('web.core');

    console.log('External image zoom script loaded');

    var $overlay = null;
    var isZoomActive = false;

    // Function to attach zoom to images
    function attachZoomToImage($img) {
        if ($img.data('zoom-attached')) {
            return; // Already attached
        }
        $img.data('zoom-attached', true);
        console.log('Attaching zoom to image:', $img[0]);
    }

    // Function to create zoom overlay
    function createZoomOverlay(imgSrc) {
        if ($overlay || isZoomActive || !imgSrc) {
            return;
        }

        console.log('Creating zoom overlay for:', imgSrc);
        isZoomActive = true;

        // Create centered overlay
        $overlay = $('<div class="external_image_zoom_overlay"></div>').css({
            'position': 'fixed',
            'top': '50%',
            'left': '50%',
            'transform': 'translate(-50%, -50%)',
            'z-index': '9999',
            'display': 'flex',
            'align-items': 'center',
            'justify-content': 'center',
            'cursor': 'zoom-out',
            'opacity': '0',
            'transition': 'opacity 0.3s ease',
            'pointer-events': 'auto'
        });

        // Create zoomed image
        var $zoomedImg = $('<img/>').attr('src', imgSrc).css({
            'max-width': '800px',
            'max-height': '600px',
            'border': '3px solid white',
            'border-radius': '8px',
            'box-shadow': '0 20px 60px rgba(0, 0, 0, 0.8)',
            'object-fit': 'contain',
            'transform': 'scale(0.9)',
            'transition': 'transform 0.3s ease',
            'pointer-events': 'none'
        });

        $overlay.append($zoomedImg);
        $('body').append($overlay);

        // Fade in animation
        setTimeout(function() {
            if ($overlay) {
                $overlay.css('opacity', '1');
                $zoomedImg.css('transform', 'scale(1)');
            }
        }, 10);
    }

    // Function to close overlay
    function closeOverlay() {
        console.log('Closing overlay');
        if ($overlay) {
            $overlay.css('opacity', '0');
            setTimeout(function() {
                if ($overlay) {
                    $overlay.remove();
                    $overlay = null;
                }
                isZoomActive = false;
            }, 300);
        } else {
            isZoomActive = false;
        }
    }

    // Function to scan and attach zoom to all zoomable images
    function scanForZoomableImages() {
        // Check in main document
        $('.external_image_zoomable').each(function() {
            attachZoomToImage($(this));
        });

        // Check in iframes (for HTML widget)
        $('iframe').each(function() {
            try {
                var iframeDoc = this.contentDocument || this.contentWindow.document;
                $(iframeDoc).find('.external_image_zoomable').each(function() {
                    attachZoomToImage($(this));
                });
            } catch(e) {
                console.log('Cannot access iframe content:', e);
            }
        });
    }

    // Use core.bus to wait for web client to be ready
    core.bus.on('web_client_ready', null, function() {
        console.log('Web client ready, attaching zoom handlers');

        // Scan for existing images
        scanForZoomableImages();

        // Set up MutationObserver to detect new content
        var observer = new MutationObserver(function(mutations) {
            scanForZoomableImages();
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        // Event delegation for mouseenter (works in main document)
        $(document).on('mouseenter', '.external_image_zoomable', function(e) {
            console.log('Mouse entered zoomable image');
            var imgSrc = $(this).attr('src');
            createZoomOverlay(imgSrc);
        });

        // Mouseleave from original image
        $(document).on('mouseleave', '.external_image_zoomable', function(e) {
            console.log('Mouse left zoomable image');
            setTimeout(function() {
                if (!$('.external_image_zoom_overlay:hover').length) {
                    closeOverlay();
                }
            }, 100);
        });

        // Click on overlay to close
        $(document).on('click', '.external_image_zoom_overlay', function(e) {
            console.log('Clicked on overlay');
            closeOverlay();
        });

        // Mouseleave from overlay
        $(document).on('mouseleave', '.external_image_zoom_overlay', function(e) {
            console.log('Mouse left overlay');
            closeOverlay();
        });

        // ESC key to close
        $(document).on('keydown', function(e) {
            if ((e.key === 'Escape' || e.keyCode === 27) && $overlay) {
                console.log('ESC pressed, closing overlay');
                closeOverlay();
            }
        });

        // Also scan periodically for new content
        setInterval(scanForZoomableImages, 2000);
    });

    return {};
});
