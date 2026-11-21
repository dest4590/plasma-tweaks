import QtQml
import "code/favoriteShortcuts.js" as FavoriteShortcuts

QtObject {
    function activate(index: int): bool {
        return FavoriteShortcuts.activate(index);
    }
}
