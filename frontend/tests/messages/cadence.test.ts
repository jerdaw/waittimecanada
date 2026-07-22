import { describe, expect, it } from "vitest";

import en from "@/messages/en.json";
import fr from "@/messages/fr.json";

describe("public cadence copy", () => {
  it("uses the hourly polling definition in both locales", () => {
    expect(en.Hero.stats.cadence).toBe("Sources Checked Hourly");
    expect(fr.Hero.stats.cadence).toBe("Sources vérifiées chaque heure");

    for (const messages of [en, fr]) {
      const serialized = JSON.stringify(messages);
      expect(serialized).not.toMatch(/fresh data every 4 hours/i);
      expect(serialized).not.toMatch(/données fraîches toutes les 4h/i);
      expect(messages.StructuredData.faq.a3).toMatch(/hour|heure/i);
      expect(messages.FAQPage.items.q4.answer).toMatch(/guarantee|garantie/i);
    }
  });

  it("defines exact and unavailable coverage labels without ellipsis fallbacks", () => {
    expect(en.Hero.stats.hospitals).toBe("{count} Hospitals");
    expect(fr.Hero.stats.hospitals).toBe("{count} hôpitaux");
    expect(en.Hero.stats.hospitalsUnavailable).toBe(
      "Hospital count unavailable",
    );
    expect(fr.Hero.stats.hospitalsUnavailable).toBe(
      "Nombre d’hôpitaux indisponible",
    );
    expect(JSON.stringify(en.Hero.stats)).not.toContain("...");
    expect(JSON.stringify(fr.Hero.stats)).not.toContain("...");
  });
});
