<?php
$token = $argv[1];
$domain = $argv[2]; // UNUSED
$url = $argv[3];
$fpath = $argv[4];

$tokenurl = $url . '?token=' . $token;

$fp = fopen($fpath, 'w');
$ch = curl_init($tokenurl);
curl_setopt($ch, CURLOPT_FILE, $fp);
$data = curl_exec($ch);
curl_close($ch);
fclose($fp);
