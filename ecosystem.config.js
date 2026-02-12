module.exports = {
  apps: [{
    name: 'inventario-tintas',
    script: '/usr/bin/python3',
    args: '-m gunicorn -w 4 -b 0.0.0.0:5010 app:app',
    cwd: '/root/inventario-excel-recuperacion',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'production',
      PORT: 5010
    },
    error_file: './logs/error.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true
  }]
};
