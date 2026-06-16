export function parseCsvRecords(text: string): Record<string, string>[] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = '';
  let quoted = false;

  const pushField = () => {
    row.push(field);
    field = '';
  };

  const pushRow = () => {
    pushField();
    if (row.some(value => value.length > 0)) {
      rows.push(row);
    }
    row = [];
  };

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (char === '"') {
      if (quoted && text[index + 1] === '"') {
        field += '"';
        index += 1;
      } else {
        quoted = !quoted;
      }
      continue;
    }
    if (char === ',' && !quoted) {
      pushField();
      continue;
    }
    if (char === '\n' && !quoted) {
      pushRow();
      continue;
    }
    if (char === '\r' && !quoted) {
      continue;
    }
    field += char;
  }
  if (field.length > 0 || row.length > 0) {
    pushRow();
  }

  const [headers, ...dataRows] = rows;
  if (!headers) return [];
  return dataRows.map(values => {
    const record: Record<string, string> = {};
    headers.forEach((header, index) => {
      record[header] = values[index] ?? '';
    });
    return record;
  });
}
