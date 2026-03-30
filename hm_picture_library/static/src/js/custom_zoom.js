odoo.define('hm_picture_library.custom_zoom', function (require) { "use strict";

    var core = require('web.core');
    var field_registry = require('web.field_registry');
    var FieldBinaryImage = require('web.basic_fields').FieldBinaryImage;

    var QWeb = core.qweb;
    var _t = core._t;

    var ZoomFieldBinaryImage = FieldBinaryImage.extend({
        init: function () {
            this._super.apply(this, arguments);
            this.zoomEnabled = this.nodeOptions.custom_image || false;
        },

        _render: function () {
            this._super.apply(this, arguments);
            if (this.zoomEnabled && this.value) {
                var $image = this.$('img');
                var imageUrl = $image.attr('src');

                var previewField = this.nodeOptions.preview_image || this.name;
                var previewImageUrl = this._getImageUrl(this.model, this.res_id, previewField, this.recordData.__last_update);

                // Determine the image URL to be used for zooming
                var imageToZoom = previewField ? previewImageUrl : imageUrl;

                var previewImage = new Image();
                previewImage.onload = function() {
                    // Get the dimensions of the preview image
                    var previewWidth = previewImage.width;
                    var previewHeight = previewImage.height;

                    $image.attr('data-zoom', 1);
                    $image.attr('data-zoom-image', imageToZoom);
                    $image.zoomOdoo({
                        event: 'mouseenter',
                        attachToTarget: true,
                        onShow: function () {
                            // Hide the zoom if it's too small
                            var zoomHeight = Math.ceil(this.$zoom.height());
                            var zoomWidth = Math.ceil(this.$zoom.width());
                            if (zoomHeight < 128 && zoomWidth < 128) {
                                this.hide();
                            }
                        },
                        beforeAttach: function () {
                          // Determine the width and height to use for zooming
                          var widthToUse = previewField ? previewWidth : $image[0].naturalWidth;
                          var heightToUse = previewField ? previewHeight : $image[0].naturalHeight;


                            // Calculate the zoom percentage based on the dimensions
                            var zoomPercentage;
                            if ((widthToUse > 500 && widthToUse < 700) || (heightToUse > 500 && heightToUse < 700)) {
                                zoomPercentage = 0.7;
                            } else if ((widthToUse >= 700 && widthToUse <= 1000) || (heightToUse >= 700 && heightToUse <= 1000)) {
                                zoomPercentage = 0.6;
                            } else if (widthToUse > 1000 || heightToUse >= 1000) {
                                zoomPercentage = 0.5;
                            } else {
                                zoomPercentage = 3;
                            }


                            // Calculate the zoomed width and height
                            var zoomWidth = Math.floor(widthToUse * zoomPercentage);
                            var zoomHeight = Math.floor(heightToUse * zoomPercentage);


                            // Set the dimensions of the zoomed image
                            this.$flyout.css({ width: zoomWidth + 'px', height: zoomHeight + 'px' });
                            var $flyoutImage = this.$flyout.find('img');

                            // Set the source of the flyout image to the appropriate URL
                            $flyoutImage.attr('src', imageToZoom);
                            $flyoutImage.css({ width: '100%', height: '100%' });
                        },
                        preventClicks: false,
                    });
                };
                previewImage.src = imageToZoom;
            }
        },
    });

    field_registry.add('custom_image', ZoomFieldBinaryImage);

    return ZoomFieldBinaryImage;
});