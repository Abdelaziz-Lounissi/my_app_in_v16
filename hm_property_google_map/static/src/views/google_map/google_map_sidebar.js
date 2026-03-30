/** @odoo-module **/

import { GoogleMapSidebar } from '@web_view_google_map/views/google_map/google_map_sidebar';

export class GoogleMapSidebarPropertyAvatar extends GoogleMapSidebar {
    getData(record) {
        const avatarUrl = `/web/image/${record.resModel}/${record.resId}/${this.props.fieldAvatar}`;
        return Object.assign({ avatarUrl }, super.getData(record));
    }
}

GoogleMapSidebarPropertyAvatar.template = 'hm_property_google_map.GoogleMapSidebarAvatar';
GoogleMapSidebarPropertyAvatar.props = [...GoogleMapSidebar.props, 'fieldAvatar'];
