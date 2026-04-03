const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

// When AGENTSIGHT_EMBED=1, output directly into the Rust crate so that
// include_dir! can pick it up at compile time.
const embedMode = process.env.AGENTSIGHT_EMBED === '1';
const outDir = embedMode
  ? path.resolve(__dirname, '../frontend-dist')
  : path.resolve(__dirname, 'dist');

module.exports = {
  mode: process.env.NODE_ENV === 'development' ? 'development' : 'production',
  entry: './src/index.tsx',
  output: {
    path: outDir,
    filename: 'bundle.[contenthash:8].js',
    clean: true,
  },
  module: {
    rules: [
      {
        test: /\.(ts|tsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              [
                '@babel/preset-react',
                {
                  development: true
                }
              ],
              '@babel/preset-env',
              '@babel/preset-typescript'
            ]
          }
        }
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader', 'postcss-loader']
      }
    ]
  },
  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.jsx']
  },
  devServer: {
    port: 3004,
    allowedHosts: ['all', '.alibaba-inc.com'],
    historyApiFallback: {
      index: '/index.html',
      rewrites: [
        { from: /^\/_p\/\d+\//, to: '/index.html' }
      ]
    }
  },
  performance: {
    hints: false
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './index.html',
      inject: 'body'
    })
  ]
};
