/** @odoo-module **/

import { registry } from '@web/core/registry';
import { googleMapPropertyAvatarView } from '@hm_property_google_map/views/google_map/google_map_view';
import { GoogleMapPlacesPropertyAvatarRenderer } from './google_map_renderer';

export const googleMapPlacesPropertyAvatarView = {
    ...googleMapPropertyAvatarView,
    Renderer: GoogleMapPlacesPropertyAvatarRenderer,
};

registry
    .category('views')
    .add('google_map_places_property_avatar', googleMapPlacesPropertyAvatarView);
