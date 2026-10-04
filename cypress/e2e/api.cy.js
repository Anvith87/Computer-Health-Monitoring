describe("PulseCore API", () => {

  it("should return system information", () => {
    cy.request("/api/system-info").then((response) => {

      expect(response.status).to.eq(200);

      expect(response.body).to.have.property("hostname");
      expect(response.body).to.have.property("os_name");
      expect(response.body).to.have.property("cpu_model");
      expect(response.body).to.have.property("physical_cores");
      expect(response.body).to.have.property("logical_cores");
      expect(response.body).to.have.property("total_ram_gb");

    });
  });

  it("should return realtime statistics", () => {
    cy.request("/api/realtime-stats").then((response) => {

      expect(response.status).to.eq(200);

      expect(response.body).to.have.property("timestamp");
      expect(response.body).to.have.property("uptime_seconds");
      expect(response.body).to.have.property("cpu_total");
      expect(response.body).to.have.property("memory");
      expect(response.body).to.have.property("disks");
      expect(response.body).to.have.property("processes");

    });
  });

  it("should return CPU data", () => {
    cy.request("/api/realtime-stats").then((response) => {

      expect(response.body.cpu_total).to.be.a("number");

      expect(response.body.cpu_total)
        .to.be.gte(0)
        .and.to.be.lte(100);

    });
  });

  it("should return valid memory data", () => {
    cy.request("/api/realtime-stats").then((response) => {

      expect(response.body.memory.percent)
        .to.be.gte(0)
        .and.to.be.lte(100);

    });
  });

  it("should return process information", () => {
    cy.request("/api/realtime-stats").then((response) => {

      expect(response.body.processes).to.be.an("array");

    });
  });

  it("should reject invalid kill-process request", () => {

    cy.request({
      method: "POST",
      url: "/api/kill-process",
      body: {},
      failOnStatusCode: false
    }).then((response) => {

      expect(response.status).to.be.oneOf([400, 422]);

    });

  });

  it("should reject invalid process ID", () => {

    cy.request({
      method: "POST",
      url: "/api/kill-process",
      body: {
        pid: -1
      },
      failOnStatusCode: false
    }).then((response) => {

      expect(response.status).to.be.oneOf([400, 422]);

    });

  });

});