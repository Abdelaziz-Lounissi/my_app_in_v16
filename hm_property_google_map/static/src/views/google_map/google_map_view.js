/** @odoo-module **/

import { registry } from '@web/core/registry';
import { googleMapView } from '@web_view_google_map/views/google_map/google_map_view';
import { GoogleMapRendererPropertyAvatar } from './google_map_renderer';
import { GoogleMapPropertyAvatarArchParser } from './google_map_arch_parser';

export const googleMapPropertyAvatarView = {
    ...googleMapView,
    ArchParser: GoogleMapPropertyAvatarArchParser,
    Renderer: GoogleMapRendererPropertyAvatar,
};

registry.category('views').add('google_map_property_avatar', googleMapPropertyAvatarView);
