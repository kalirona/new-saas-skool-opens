// LearnHouse PM2 Ecosystem Config
// Zero-downtime with graceful reload: pm2 reload ecosystem.config.js
//
// Usage:
//   pm2 start ecosystem.config.js --env production
//   pm2 reload ecosystem.config.js  (zero-downtime reload)

module.exports = {
  apps: [
    {
      name: 'learnhouse-api',
      script: 'uv',
      args: 'run uvicorn app:app --host 0.0.0.0 --port 9000 --workers 4 --timeout-keep-alive 600',
      cwd: './apps/api',
      interpreter: 'none',
      instances: 2,
      exec_mode: 'cluster',
      max_restarts: 10,
      restart_delay: 5000,
      min_uptime: 10000,
      watch: false,
      kill_timeout: 10000,
      listen_timeout: 30000,
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1',
        PYTHONIOENCODING: 'utf-8',
      },
      env_production: {
        LEARNHOUSE_DEVELOPMENT_MODE: 'false',
        LEARNHOUSE_LOG_LEVEL: 'INFO',
      },
      error_file: './logs/pm2/api-error.log',
      out_file: './logs/pm2/api-out.log',
      merge_logs: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },
  ],
};
