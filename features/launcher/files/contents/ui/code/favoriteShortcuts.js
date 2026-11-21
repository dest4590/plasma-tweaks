.pragma library

let launcher = null;

function setExpanded(item, expanded) {
    if (expanded) {
        launcher = item;
    } else if (launcher === item) {
        launcher = null;
    }
}

function activate(index) {
    if (!launcher || !launcher.expanded) {
        return false;
    }

    const item = launcher;
    const favorites = item.rootModel.favoritesModel;
    if (index >= 0 && index < favorites.count && favorites.trigger(index, "", null)) {
        if (item.hideOnWindowDeactivate) {
            item.expanded = false;
        }
    }
    return true;
}
