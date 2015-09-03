MAILTO="howep@emc.com"

*/5 * * * * root [ -x /usr/local/mcp/cron/fullIterate ] && /usr/local/mcp/cron/fullIterate
*/1 * * * * root [ -x /usr/local/mcp/cron/iterate ] && /usr/local/mcp/cron/iterate
