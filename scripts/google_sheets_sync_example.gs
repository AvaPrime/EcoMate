/**
 * Create a Google Sheet, then Tools > Script editor, paste this, set GITHUB_RAW_URL, run `sync()`.
 * This pulls CSV from GitHub and overwrites a sheet tab named `data`.
 */
const GITHUB_RAW_URL = 'https://raw.githubusercontent.com/YOURORG/ecomate-docs/main/data/suppliers.csv';

function sync() {
  const resp = UrlFetchApp.fetch(GITHUB_RAW_URL);
  const csv = Utilities.parseCsv(resp.getContentText());
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName('data') || ss.insertSheet('data');
  sh.clearContents();
  sh.getRange(1,1,csv.length,csv[0].length).setValues(csv);
}