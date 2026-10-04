// Cypress global configuration and reusable commands

Cypress.Commands.add("mockSystemInfo", () => {
  cy.intercept("GET", "/api/system-info", {
    statusCode: 200,
    body: {
      hostname: "TEST-PC",
      os_name: "Windows",
      os_version: "11",
      architecture: "64bit",
      cpu_model: "AMD Ryzen 3 3250U",
     physical_cores: 2,
      logical_cores: 4,
      total_ram_gb: 8,
      boot_time: "2026-09-27 08:00:00",
    },
  }).as("systemInfo");
});

Cypress.Commands.add("mockRealtimeStats", () => {
  cy.intercept("GET", "/api/realtime-stats", {
    statusCode: 200,
    body: {
      timestamp: "2026-09-27T12:00:00",
      uptime_seconds: 3600,

      cpu_total: 35.5,
      cpu_cores: [30.2, 40.8, 35.1, 36.0],

      memory: {
        total_gb: 8,
        used_gb: 4,
        available_gb: 4,
        free_gb: 3,
        percent: 50,
      },

      swap: {
        total_gb: 2,
        used_gb: 0.5,
        percent: 25,
      },

      disks: [
        {
          device: "C:",
          mountpoint: "C:\\",
          fstype: "NTFS",
          total_gb: 476,
          used_gb: 200,
          free_gb: 276,
          percent: 42,
        },
      ],

      disk_io: {
        read_bytes_per_sec: 1024,
        write_bytes_per_sec: 2048,
        cumulative_read_bytes: 1073741824,
        cumulative_write_bytes: 2147483648,
        read_count: 100,
        write_count: 50,
      },

      net_io: {
        bytes_sent_per_sec: 100,
        bytes_recv_per_sec: 200,
        cumulative_sent_bytes: 10000,
        cumulative_recv_bytes: 20000,
      },

      battery: {
        percent: 80,
        power_plugged: true,
        secs_left: null,
      },

      processes_count: 2,

      processes: [
        {
          pid: 1234,
          name: "Chrome",
          cpu: 25.5,
          mem_mb: 500.1,
          mem_percent: 6.2,
          user: "test",
        },
        {
          pid: 5678,
          name: "Python",
          cpu: 10.2,
          mem_mb: 100.5,
          mem_percent: 1.3,
          user: "test",
        },
      ],
    },
  }).as("realtimeStats");
});