const path = require('path');

module.exports = {
  context: path.resolve(__dirname, 'app'),
  entry: {
    base: './static/js/base.js',
    datasets: './static/js/datasets.js',
    fairness: './static/js/fairness.js',
    inspect: './static/js/inspect.js',
    profile: './static/js/profile.js',
    sidebars: './static/js/sidebars.js',
  },
  externals: {
    // only define the dependencies you are NOT using as externals!
    canvg: "canvg",
    html2canvas: "html2canvas",
    dompurify: "dompurify"
  },
  output: {
    filename: '[name].js',
    path: path.resolve(__dirname, 'static')
  }
};