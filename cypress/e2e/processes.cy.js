describe("PulseCore Process Management", () => {

  beforeEach(() => {
    cy.mockSystemInfo();
    cy.mockRealtimeStats();

    cy.visit("/");

    cy.wait("@systemInfo");
    cy.wait("@realtimeStats");

    cy.contains("Processes").click();
  });

  it("should display process table", () => {
    cy.get("#allProcessesTable").should("exist");
  });

  it("should display Chrome process", () => {
    cy.get("#allProcessesTable")
      .should("contain.text", "Chrome");
  });

  it("should display Python process", () => {
    cy.get("#allProcessesTable")
      .should("contain.text", "Python");
  });

  it("should allow process searching", () => {
    cy.get("#procSearchInput")
      .type("Chrome");

    cy.get("#allProcessesTable")
      .should("contain.text", "Chrome");
  });

  it("should filter out unrelated processes", () => {
    cy.get("#procSearchInput")
      .type("Chrome");

    cy.get("#allProcessesTable")
      .should("contain.text", "Chrome")
      .and("not.contain.text", "Python");
  });

  it("should have process sorting control", () => {
    cy.get("#procSortBy").should("exist");
  });

  it("should sort processes by CPU", () => {
    cy.get("#procSortBy").select("cpu");

    cy.get("#allProcessesTable").should("exist");
  });

});