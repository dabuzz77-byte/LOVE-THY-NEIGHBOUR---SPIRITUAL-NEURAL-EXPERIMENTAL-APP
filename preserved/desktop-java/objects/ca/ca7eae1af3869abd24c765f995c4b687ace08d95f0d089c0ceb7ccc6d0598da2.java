module system.monitor {
    requires javafx.controls;
    requires javafx.graphics;
    requires javafx.fxml;

    // Export your namespaces explicitly
    exports app;
    exports model;
    exports service;
    exports view;

    opens view to javafx.graphics, javafx.base;
    opens app to javafx.graphics;
}
