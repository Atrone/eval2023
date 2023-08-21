module.exports = function override(config, env) {
  config.resolve = config.resolve || {};
  config.resolve.alias = config.resolve.alias || {};
  config.resolve.alias['stream'] = 'stream-browserify';
  return config;
};
