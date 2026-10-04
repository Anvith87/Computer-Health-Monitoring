describe("PulseCore Dashboard", () => {

  beforeEach(() => {
    cy.mockSystemInfo();
    cy.mockRealtimeStats();

    cy.visit("/");

    cy.wait("@systemInfo");
    cy.wait("@realtimeStats");
  });

  it("should load the PulseCore dashboard", () => {
    cy.title().should("not.be.empty");

    cy.get("body").should("be.visible");
  });

  it("should display system information", () => {
    cy.get("body").should("contain.text", "TEST-PC");

    cy.get("body").should("contain.text", "AMD Ryzen 3 3250U");
  });

  it("should display CPU information", () => {
    cy.get("body").should("contain.text", "35.5");
  });

  it("should display memory information", () => {
    cy.get("body").should("contain.text", "8");
  });

  it("should display battery information", () => {
    cy.get("body").should("contain.text", "80");
  });

  it("should display process information", () => {
    cy.get("body").should("contain.text", "Chrome");
    cy.get("body").should("contain.text", "Python");
  });

});