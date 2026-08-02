/**
 * Weekly operating-hours parser for Google Maps ARIA snapshots.
 *
 * Parses the expanded hours subtree: weekday rows of the form
 *   - row "Sunday 10 AM to 10 PM, ...":
 *     - cell "Sunday"
 *     - cell "10 AM to 10 PM"
 *     - cell "Copy open hours"
 *
 * Normalizes schedules without inventing missing values. Supports closed days,
 * 24-hour operation, split schedules, overnight closing, and holiday exceptions.
 */

export type TimePeriod = {
  opens: string; // "HH:MM" 24h
  closes: string; // "HH:MM" 24h
  closesNextDay: boolean;
};

export type DaySchedule = {
  day: string; // lowercase weekday
  displayDay?: string;
  closed: boolean;
  open24Hours: boolean;
  periods: TimePeriod[];
  exception?: {
    label: string;
    hoursMightDiffer?: boolean;
  };
};

export type WeeklySchedule = {
  [day: string]: DaySchedule;
};

export type ParsedHours = {
  weekly: WeeklySchedule;
  specialHours: { displayDay: string; raw: string }[];
  rawRows: string[];
  completeness: "complete" | "partial";
  missingDays: string[];
  timezone: string;
};

export const WEEKDAYS = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday",
];

const WEEKDAY_LABELS: Record<string, string> = {
  monday: "Monday",
  tuesday: "Tuesday",
  wednesday: "Wednesday",
  thursday: "Thursday",
  friday: "Friday",
  saturday: "Saturday",
  sunday: "Sunday",
};

const TIME_RE = /^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$/i;

export class HoursParseError extends Error {}

/**
 * Convert "10 AM", "10:30 PM", "12 AM", "12 PM" to 24h "HH:MM".
 *
 * A meridian-less "12" is ambiguous: Google sometimes writes "12 to 10 PM"
 * meaning noon to 10 PM. When the meridian is absent, callers pass a hint
 * (the closing meridian) so "12" resolves to 12:00 if closing is PM, or 00:00
 * if closing is AM.
 */
export function parseTime(value: string, hintMeridian?: string): string {
  const m = value.trim().match(TIME_RE);
  if (!m) throw new HoursParseError(`Malformed time: ${value}`);
  let hour = parseInt(m[1]!, 10);
  const minute = m[2] ? parseInt(m[2], 10) : 0;
  const explicitMeridian = m[3];
  if (hour < 1 || hour > 12) throw new HoursParseError(`Invalid hour: ${value}`);
  if (minute < 0 || minute > 59) throw new HoursParseError(`Invalid minute: ${value}`);

  // Bare hour with no meridian at all: Google writes "12 to 10 PM" meaning
  // noon. A bare "12" is noon; a bare non-12 hour with a PM hint is that hour PM.
  if (!explicitMeridian) {
    const meridian = (hintMeridian || "").toLowerCase();
    if (meridian === "am") {
      if (hour === 12) hour = 0;
      return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
    }
    if (hour === 12) {
      // bare 12 + PM = noon
      return `12:${String(minute).padStart(2, "0")}`;
    }
    // bare non-12 + PM hint = that hour PM
    return `${String(hour + 12).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
  }

  const meridian = explicitMeridian.toLowerCase();
  if (meridian === "am") {
    if (hour === 12) hour = 0;
  } else {
    if (hour !== 12) hour += 12;
  }
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
}

/**
 * Parse a single interval like "10 AM to 10 PM" or "10 AM–10:30 PM".
 * Handles en/em dashes (with or without surrounding spaces) and the word "to".
 */
export function parseInterval(text: string): TimePeriod | null {
  const clean = text.trim().replace(/\s+/g, " ");
  // "10 AM to 10 PM", "10 AM–10 PM", "12 to 10 PM", "12–11 PM"
  const m = clean.match(/^(.+?)(?:\s+to\s+|\s*[–—\-]\s*)(.+)$/i);
  if (!m) return null;
  try {
    // If the closing time carries a meridian, use it as a hint for a bare
    // opening time (e.g. "12 to 10 PM" -> noon).
    const close = m[2]!;
    const closeMeridian = close.match(/(am|pm)/i)?.[1];
    const opens = parseTime(m[1]!, closeMeridian);
    const closes = parseTime(close, closeMeridian);
    const closesNextDay = closes < opens;
    return { opens, closes, closesNextDay };
  } catch {
    return null;
  }
}

/**
 * Parse a holiday parenthetical from a day label, e.g. "Sunday (Virgen de los Ángeles)".
 */
export function parseHolidayLabel(dayLabel: string): string | null {
  const m = dayLabel.match(/\(([^)]+)\)/);
  return m ? m[1]!.trim() : null;
}

/**
 * Normalize a weekday label to lowercase English. Returns null if unrecognized.
 */
export function parseWeekdayLabel(label: string): string | null {
  const l = label.trim().toLowerCase();
  const known = WEEKDAYS.find((d) => l === d || l.startsWith(d));
  if (known) return known;
  // Handle "Sunday (Holiday)" and similar prefixes.
  for (const d of WEEKDAYS) {
    if (l.startsWith(d)) return d;
  }
  return null;
}

/**
 * Parse a single ARIA weekday row into a DaySchedule.
 *
 * Example rows:
 *   "Sunday (Virgen de los Ángeles) 10 AM to 10 PM, Hours might differ"
 *   "Tuesday Closed"
 *   "Wednesday Open 24 hours"
 *   "Friday 4 PM to 2:30 AM"
 */
export function parseDayRow(rowText: string): DaySchedule {
  const rawRow = rowText.trim().replace(/\s{2,}/g, " ");
  // Extract the leading weekday label: "Tuesday" or "Sunday (Virgen de los Ángeles)".
  const labelMatch = rawRow.match(/^(Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)(\([^)]*\))?/i);
  const dayLabel = (labelMatch ? labelMatch[0] : "").trim();
  const day = parseWeekdayLabel(dayLabel);
  if (!day) throw new HoursParseError(`Unrecognized weekday in row: ${rowText}`);

  // Clean display day: "Monday" or "Sunday (Virgen de los Ángeles)".
  const displayDay = dayLabel;
  const holiday = parseHolidayLabel(dayLabel);
  const hoursMightDiffer = /hours might differ/i.test(rowText);
  const isClosed = /(^|\s)closed(\s|$)/i.test(rowText);
  const open24 = /open 24 hours/i.test(rowText);

  if (isClosed) {
    return {
      day,
      displayDay,
      closed: true,
      open24Hours: false,
      periods: [],
      exception: holiday ? { label: holiday, hoursMightDiffer } : undefined,
    };
  }

  if (open24) {
    return {
      day,
      displayDay,
      closed: false,
      open24Hours: true,
      periods: [{ opens: "00:00", closes: "24:00", closesNextDay: false }],
      exception: holiday ? { label: holiday, hoursMightDiffer } : undefined,
    };
  }

  // Collect all intervals in the row. The row accessible name repeats the
  // schedule (e.g. "Monday 10 AM to 10 PM Monday, 10 AM to 10 PM, Copy open
  // hours"), so exact duplicates are deduplicated.
  const intervals: TimePeriod[] = [];
  const tokens = rowText.replace(/Copy open hours/g, "").replace(/Hours might differ/g, "");
  // Find every "X AM to Y PM" / "X AM–Y PM" segment.
  const segRe = /\b\d{1,2}(?::\d{2})?\s*(?:am|pm)?(?:\s+to\s+|\s*[–—\-]\s*)\d{1,2}(?::\d{2})?\s*(?:am|pm)\b/gi;
  let mm: RegExpExecArray | null;
  const segments: string[] = [];
  while ((mm = segRe.exec(tokens)) !== null) {
    segments.push(mm[0]);
  }
  if (segments.length === 0) {
    throw new HoursParseError(`No parseable interval in row: ${rowText}`);
  }
  const seen = new Set<string>();
  for (const seg of segments) {
    const p = parseInterval(seg);
    if (!p) continue;
    const key = `${p.opens}|${p.closes}`;
    if (seen.has(key)) continue;
    seen.add(key);
    intervals.push(p);
  }
  if (intervals.length === 0) {
    throw new HoursParseError(`Intervals did not parse in row: ${rowText}`);
  }

  return {
    day,
    displayDay,
    closed: false,
    open24Hours: false,
    periods: intervals,
    exception: holiday ? { label: holiday, hoursMightDiffer } : undefined,
  };
}

/**
 * Parse the full set of weekday rows from an ARIA snapshot.
 *
 * Accepts either `- row "..."` lines (the expanded hours table) or, as a
 * fallback, the `button "Hours ..."` subtree lines that contain weekday text.
 */
export function parseHoursAria(snapshot: string): ParsedHours {
  const lines = snapshot.split("\n");
  const rowLines = lines
    .filter((l) => /-\s+row\s+"/.test(l))
    .map((l) => {
      // Row names may contain escaped quotes; capture the full quoted span.
      const m = l.match(/-\s+row\s+"((?:\\.|[^"\\])*)"/);
      return m ? m[1]!.replace(/\\(.)/g, "$1").trim() : "";
    })
    .filter(Boolean);

  const rawRows = rowLines.filter((r) => WEEKDAYS.some((d) => r.toLowerCase().startsWith(d)));

  const weekly: WeeklySchedule = {};
  const specialHours: ParsedHours["specialHours"] = [];

  for (const row of rawRows) {
    try {
      const parsed = parseDayRow(row);
      if (parsed.exception) {
        specialHours.push({ displayDay: parsed.displayDay || row, raw: row });
      }
      // Keep the canonical day schedule; exceptions preserved separately.
      weekly[parsed.day] = parsed;
    } catch (err) {
      if (err instanceof HoursParseError) {
        specialHours.push({ displayDay: row.slice(0, 40), raw: row });
      } else {
        throw err;
      }
    }
  }

  const missingDays = WEEKDAYS.filter((d) => !weekly[d]);
  const completeness = missingDays.length === 0 ? "complete" : "partial";

  return {
    weekly,
    specialHours,
    rawRows,
    completeness,
    missingDays,
    timezone: "America/Costa_Rica",
  };
}

/**
 * Validate a parsed schedule's internal consistency.
 * Throws on contradictions (e.g. closed day with periods, 24h day marked closed).
 */
export function validateWeeklySchedule(schedule: WeeklySchedule): void {
  for (const day of WEEKDAYS) {
    const d = schedule[day];
    if (!d) continue;
    if (d.closed && d.periods.length > 0) {
      throw new HoursParseError(`${day}: closed but has ${d.periods.length} periods`);
    }
    if (d.open24Hours && d.closed) {
      throw new HoursParseError(`${day}: open 24 hours but marked closed`);
    }
    if (d.closed && d.open24Hours) {
      throw new HoursParseError(`${day}: both closed and open 24 hours`);
    }
  }
}
