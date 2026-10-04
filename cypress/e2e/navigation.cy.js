describe("PulseCore Navigation", () => {

  beforeEach(() => {
    cy.mockSystemInfo();
    cy.mockRealtimeStats();

    cy.visit("/");

    cy.wait("@systemInfo");
    cy.wait("@realtimeStats");
  });

  it("should display Overview tab", () => {
    cy.get("#tab-overview").should("exist");
  });

  it("should navigate to Processes", () => {
    cy.contains("Processes").click();

    cy.get("#tab-processes").should("be.visible");
  });

  it("should navigate to Storage", () => {
    cy.contains("Storage").click();

    cy.get("#tab-storage").should("be.visible");
  });

  it("should navigate to Specs", () => {
    cy.contains("Specs").click();

    cy.get("#tab-specs").should("be.visible");
  });

  it("should return to Overview", () => {
    cy.contains("Processes").click();

    cy.contains("Overview").click();

    cy.get("#tab-overview").should("be.visible");
  });

});