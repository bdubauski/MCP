MAILTO="howep@emc.com"

*/1 * * * * root [ -x /usr/local/plato/cron/iterate ] && /usr/local/plato/cron/iterate
*/5 * * * * root [ -x /usr/local/plato/cron/fullIterate ] && /usr/local/plato/cron/fullIterate
