class GraphManager {
    constructor() {
        this.devices = [];
    }

    async initialize() {
        console.log('🚀 Frequency Graphs Test Site - Ready!');
        console.log('📈 Testing environment for frequency response graphs');
        console.log('🔧 This is separate from production site');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    window.graphManager = new GraphManager();
    window.graphManager.initialize();
});
