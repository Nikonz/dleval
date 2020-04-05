<?php
$token = $argv[1];
$domain = $argv[2];
$courseid = $argv[3];

$functionname = 'mod_assign_get_assignments';
$params = array('courseids' => array($courseid));

header('Content-Type: text/plain');
$serverurl = $domain . '/webservice/rest/server.php'. '?wstoken=' . $token . '&wsfunction='.$functionname;

require_once('php/curl.php');

$curl = new curl;
$restformat = '&moodlewsrestformat=json';
$resp = $curl->post($serverurl . $restformat, $params);
print_r($resp);