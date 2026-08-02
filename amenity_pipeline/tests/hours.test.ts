import { describe, expect, it } from "vitest";
import {
  parseTime,
  parseInterval,
  parseDayRow,
  parseHoursAria,
  validateWeeklySchedule,
  WEEKDAYS,
} from "../src/hours.js";

function snapshot(rows: string[]): string {
  const rowLines = rows.map((r) => `- row "${r}":`).join("\n");
  return `- main "Place"\n- button "Hours Show open hours for the week" [expanded]:\n${rowLines}`;
}

describe("parseTime", () => {
  it("converts 12-hour times to 24h", () => {
    expect(parseTime("10 AM")).toBe("10:00");
    expect(parseTime("10:30 PM")).toBe("22:30");
    expect(parseTime("12 AM")).toBe("00:00");
    expect(parseTime("12 PM")).toBe("12:00");
    expect(parseTime("8 AM")).toBe("08:00");
  });
  it("rejects malformed times", () => {
    expect(() => parseTime("25 AM")).toThrow();
    expect(() => parseTime("10:75 PM")).toThrow();
    expect(() => parseTime("banana")).toThrow();
  });
  it("accepts meridian-less hour with PM hint", () => {
    expect(parseTime("10", "pm")).toBe("22:00");
    expect(parseTime("12", "pm")).toBe("12:00");
  });
});

describe("parseInterval", () => {
  it("parses a normal interval", () => {
    expect(parseInterval("10 AM to 10 PM")).toEqual({ opens: "10:00", closes: "22:00", closesNextDay: false });
  });
  it("parses en-dash and em-dash", () => {
    expect(parseInterval("10 AM–10 PM")).toEqual({ opens: "10:00", closes: "22:00", closesNextDay: false });
    expect(parseInterval("10 AM—10 PM")).toEqual({ opens: "10:00", closes: "22:00", closesNextDay: false });
  });
  it("detects overnight", () => {
    expect(parseInterval("4 PM to 2:30 AM")).toEqual({ opens: "16:00", closes: "02:30", closesNextDay: true });
  });
  it("returns null for unparseable", () => {
    expect(parseInterval("garbage")).toBeNull();
  });
});

describe("parseDayRow", () => {
  it("parses a normal day", () => {
    const d = parseDayRow("Monday 10 AM to 10 PM Monday, 10 AM to 10 PM, Copy open hours");
    expect(d.day).toBe("monday");
    expect(d.closed).toBe(false);
    expect(d.periods).toEqual([{ opens: "10:00", closes: "22:00", closesNextDay: false }]);
  });
  it("parses a closed day", () => {
    const d = parseDayRow("Tuesday Closed Tuesday, Closed, Copy open hours");
    expect(d.closed).toBe(true);
    expect(d.periods).toEqual([]);
  });
  it("parses open 24 hours", () => {
    const d = parseDayRow("Wednesday Open 24 hours");
    expect(d.open24Hours).toBe(true);
    expect(d.periods).toEqual([{ opens: "00:00", closes: "24:00", closesNextDay: false }]);
  });
  it("parses split schedule", () => {
    const d = parseDayRow("Monday 8 AM to 12 PM 2 PM to 10 PM Monday, 8 AM to 12 PM, 2 PM to 10 PM, Copy open hours");
    expect(d.periods).toEqual([
      { opens: "08:00", closes: "12:00", closesNextDay: false },
      { opens: "14:00", closes: "22:00", closesNextDay: false },
    ]);
  });
  it("parses overnight", () => {
    const d = parseDayRow("Friday 4 PM to 2:30 AM Friday, 4 PM to 2:30 AM, Copy open hours");
    expect(d.periods).toEqual([{ opens: "16:00", closes: "02:30", closesNextDay: true }]);
  });
  it("parses holiday exception", () => {
    const d = parseDayRow("Sunday (Virgen de los Ángeles) 10 AM to 10 PM, Hours might differ Sunday (Virgen de los Ángeles), 10 AM to 10 PM, Hours might differ, Copy open hours");
    expect(d.day).toBe("sunday");
    expect(d.exception).toEqual({ label: "Virgen de los Ángeles", hoursMightDiffer: true });
    expect(d.periods).toEqual([{ opens: "10:00", closes: "22:00", closesNextDay: false }]);
  });
  it("parses meridian-less opening time (12 to 10 PM = noon)", () => {
    const d = parseDayRow("Monday 12 to 10 PM Monday, 12 to 10 PM, Copy open hours");
    expect(d.periods).toEqual([{ opens: "12:00", closes: "22:00", closesNextDay: false }]);
  });
  it("parses meridian-less opening time (12 to 11 PM = noon)", () => {
    expect(parseInterval("12 to 11 PM")).toEqual({ opens: "12:00", closes: "23:00", closesNextDay: false });
  });
  it("rejects unrecognized weekday", () => {
    expect(() => parseDayRow("Funday 10 AM to 10 PM")).toThrow();
  });
});

describe("parseHoursAria", () => {
  it("parses a full seven-day schedule", () => {
    const rows = [
      "Sunday 10 AM to 10 PM Sunday, 10 AM to 10 PM, Copy open hours",
      "Monday 10 AM to 10 PM Monday, 10 AM to 10 PM, Copy open hours",
      "Tuesday Closed Tuesday, Closed, Copy open hours",
      "Wednesday 10 AM to 10 PM Wednesday, 10 AM to 10 PM, Copy open hours",
      "Thursday 10 AM to 10 PM Thursday, 10 AM to 10 PM, Copy open hours",
      "Friday 10 AM to 10 PM Friday, 10 AM to 10 PM, Copy open hours",
      "Saturday 10 AM to 10:30 PM Saturday, 10 AM to 10:30 PM, Copy open hours",
    ];
    const parsed = parseHoursAria(snapshot(rows));
    expect(parsed.completeness).toBe("complete");
    expect(parsed.missingDays).toEqual([]);
    expect(Object.keys(parsed.weekly).sort()).toEqual([...WEEKDAYS].sort());
    expect(parsed.weekly.tuesday?.closed).toBe(true);
    expect(parsed.weekly.saturday?.periods[0]?.closes).toBe("22:30");
  });
  it("flags partial schedules without fabricating days", () => {
    const parsed = parseHoursAria(snapshot(["Monday 10 AM to 10 PM Monday, 10 AM to 10 PM"]));
    expect(parsed.completeness).toBe("partial");
    expect(parsed.missingDays).toContain("tuesday");
    expect(parsed.weekly.tuesday).toBeUndefined();
  });
  it("returns empty when no rows present", () => {
    const parsed = parseHoursAria("- main X\n- button Hours");
    expect(Object.keys(parsed.weekly)).toHaveLength(0);
    expect(parsed.completeness).toBe("partial");
  });
  it("handles holiday warning rows without corrupting the schedule", () => {
    const rows = [
      "Sunday (Virgen de los Ángeles) 10 AM to 10 PM, Hours might differ Sunday (Virgen de los Ángeles), 10 AM to 10 PM, Hours might differ, Copy open hours",
      "Monday 10 AM to 10 PM Monday, 10 AM to 10 PM, Copy open hours",
    ];
    const parsed = parseHoursAria(snapshot(rows));
    expect(parsed.weekly.sunday?.exception?.label).toBe("Virgen de los Ángeles");
    expect(parsed.weekly.sunday?.periods[0]?.opens).toBe("10:00");
    expect(parsed.specialHours.length).toBeGreaterThan(0);
  });
});

describe("validateWeeklySchedule", () => {
  it("accepts a valid schedule", () => {
    const s = {
      monday: { day: "monday", closed: false, open24Hours: false, periods: [{ opens: "10:00", closes: "22:00", closesNextDay: false }] },
      tuesday: { day: "tuesday", closed: true, open24Hours: false, periods: [] },
    };
    expect(() => validateWeeklySchedule(s)).not.toThrow();
  });
  it("rejects closed day with periods", () => {
    const s = {
      monday: { day: "monday", closed: true, open24Hours: false, periods: [{ opens: "10:00", closes: "22:00", closesNextDay: false }] },
    };
    expect(() => validateWeeklySchedule(s)).toThrow();
  });
  it("rejects 24h day marked closed", () => {
    const s = {
      monday: { day: "monday", closed: true, open24Hours: true, periods: [] },
    };
    expect(() => validateWeeklySchedule(s)).toThrow();
  });
});
