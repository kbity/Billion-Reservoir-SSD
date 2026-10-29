<!doctype html>
<html>
<head>
<title>"Billion Reservoir" SSD</title>

<?php
$tovr = $_GET['t'] ?? 'none';

$themes = ['default', 'bare', 'dark', 'default-noicns', 'maricom', 'maricom-dusk', 'maricom-night', 'maricom-dawn', 'aislop'];

$t = (time()-14400)%86400; // bias to UTC-4, then modulo to day progress

if (in_array($tovr, $themes)) {
  echo "<link rel=\"stylesheet\" href=\"/brthemes/$tovr.css\">";
  $theme = '&t='.$tovr;
  $thhn = '?t='.$tovr;
} else {
  if (21600 > $t || $t > 72000) { // before 6 AM or after 8 PM
    echo "<link rel=\"stylesheet\" href=\"/brthemes/maricom-night.css\">";
  } elseif (32400 > $t) { // before 9 AM
    echo "<link rel=\"stylesheet\" href=\"/brthemes/maricom-dawn.css\">";
  } elseif ($t > 61200) {  // after 5 PM
    echo "<link rel=\"stylesheet\" href=\"/brthemes/maricom-dusk.css\">";
  } else {
    echo "<link rel=\"stylesheet\" href=\"/brthemes/maricom.css\">";
  };
  $theme = '';
  $thhn = '';
};
?>

</head>

<body>
<div class=header>
<h1 class=titletext><a class=titletext href="/br.php<?=$thhn?>">"Billion Reservoir" SSD</a></h1>

<form action="/br.php" method="get" id="search">
    <input type="hidden" name="u" value="<?php $user = $_GET['u'] ?? ''; echo $user;?>" />
    <input type="hidden" name="t" value="<?php $thn = $_GET['t'] ?? ''; echo $thn;?>" />
    <input type="text" name="q" class="searchbox" placeholder="Search..." value=<?php $search = $_GET['q'] ?? ''; echo $search;?>>
    <button type="submit">Search</button>
</form>

</div>
<div class=content>
<table>
<thead>
<tr>
    <th>Name</th>
    <th>Last modified</th>
    <th>Size</th>
</tr>
</thead>

<tbody id="filelist">
<?php
$base_path = '/var/www/html/br/'; // base folder to search
$user = $_GET['u'] ?? '';

$path = $base_path.'/'.$user;
$files = [];
$search = $_GET['q'] ?? '';

$ftypes = json_decode('{"img":[".png",".apng",".jpg",".jpe",".jpeg",".gif",".gifv",".bmp",".dib",".ico",".cur",".ani",".xbm",".xpm",".pbm",".pgm",".ppm",".pam",".pfm",".pnm",".apf",".apf2",".af2",".aif2",".ap2",".aif",".fits",".flif",".flf",".fuif",".j",".jxl",".jpxl",".jxll",".jpegxl",".webp",".wbp",".jxr",".hdp",".wmp",".wbmp",".wbitmap",".wbm",".bruh",".heif",".heic",".avif",".avifs",".tiff",".tif",".bpg",".mqi",".mqif",".qoi",".kq1",".kqi",".fli",".flc",".flx",".svg",".svgz",".psd",".xcf",".farbfeld",".farb",".pcx",".tga",".dds",".jls",".jp2",".j2k",".jpf",".jpx",".jpm",".mj2",".jbg",".jb2",".mng",".ota",".otb",".rgb",".rgba",".sgi",".odg",".fodg",".ff",".fif",".ljpg",".ljpeg",".jfif",".a2k",".ap2k",".aq2",".a2g",".a2b",".a2c",".a2ci",".qlic"],"aud":[".ogg",".oga",".opus",".spx",".xm",".wv",".wvc",".m4a",".m4b",".m4p",".aac",".alac",".mp1",".mp2",".mp3",".wma",".mod",".stm",".s3m",".it",".mid",".midi",".wav",".rf64",".aiff",".aif",".aifc",".flac",".ape",".mac",".aa3",".aea",".at3",".at9",".atp",".hma",".oma",".omg",".fur",".mptm",".ecdc",".mpc",".ra",".rm",".ram",".amr",".tta",".ofr",".ofs",".g722",".g726",".g711",".g729",".lbc",".pcm",".snd",".au",".aaf"],"vid":[".avi",".webm",".wbm",".mkv",".ogv",".ogx",".mp4",".m4v",".ts",".m2ts",".mts",".mpg",".m2p",".mpeg",".vob",".m1v",".m2v",".vro",".m4s",".mov",".qtf",".qtff",".qti",".qif",".3gp",".3g2",".nut",".fmv",".bik",".smk",".bk2",".mjpg"],"doc":[".txt",".mcv",".json",".xml",".jsn",".text",".md",".odf",".fodt",".odp",".fodp",".ods",".fods",".docx",".docm",".pptx",".pptm",".xlsx",".xlsm",".rtf",".pdf",".doc",".eps",".epub",".abw",".py",".js",".log"],"arc":[".zip",".rar",".7z",".tar",".gz",".xz",".zst",".a",".ar",".cpio",".shar",".lbr",".mar",".sbx",".bz2",".z",".br",".bz2",".F",".genozip",".lz",".lz4",".lzma",".lzo",".rz",".sfark",".sz",".s7z",".aar",".ace",".afa",".alz",".arc",".ark",".cdx",".arj",".b1",".b6z",".ba",".bh",".cab",".car",".cfs",".cpt",".dar",".dd",".dgc",".dmg",".apk",".ear",".gca",".ha",".hki",".ice",".jar",".kgb",".lzh",".lza",".lzx",".pak",".partimg",".paq6",".paq7",".paq8",".pea",".phar",".pim",".pit",".qda",".rk",".sda",".sea",".sen",".sfx",".shk",".sit",".sitx",".sqx",".tgz",".uc",".uc0",".uc2",".ucn",".ur2",".ue2",".uca",".uha",".war",".wim",".xar",".xp3",".yz1",".zipx",".zoo",".zpaq",".zz",".ecc",".ecsbx",".fec",".par",".par2",".rev",".sq"]}', true);

if ($user === '') {
    $files[] = [
        'name' => '*',
        'mtime' => 0,
        'size' => '-',
        'isfolder' => true
    ];
}

// Read directory
if ($user === '*') {
    if ($handle = opendir($base_path)) {
        while (($entry = readdir($handle)) !== false) {
            if ($entry === '.' || $entry === '..') {
                continue;
            }

            $full = $base_path.'/'.$entry;

            $mcvdat = file_get_contents($base_path.'/info.mcv');
            $mcvarr = preg_split("/\r\n|\n|\r/", $mcvdat);
            $mcv = [];
            foreach ($mcvarr as $k) {
                if (substr($k, 0, 1) !== '#') {
                    $waow = explode('=', $k, 2);
                    $mcv[$waow[0]] = $waow[1];
                }
            }

            if (!is_dir($full)) {
                continue;
            }

            if ($handle2 = opendir($full)) {
                while (($entry2 = readdir($handle2)) !== false) {
                    if ($entry2 === "." || $entry2 === "..") continue;
                    $full2 = $full.'/'.$entry2;

                    if (str_contains(strtolower($entry2), strtolower($search))) { // add thing if it is in search query
                        $files[] = [
                            'name' => $entry.'/'.$entry2,
                            'mtime' => filemtime($full2),
                            'size' => filesize($full2),
                            'desc' => '',
                            'isfolder' => is_dir($full2),
                            'showname' => $mcv[$entry].'/'.$entry2
                        ];
                    }
                }
            }
            closedir($handle2);
        }
        closedir($handle);
    }
} else {
    if ($handle = opendir($path)) {
        while (($entry = readdir($handle)) !== false) {
            if ($entry === "." || $entry === ".." || $path.$entry === $base_path.'/info.mcv' || $path.$entry === $base_path.'/index.php') continue; // skip parent/hidden/internal data

            $full = $path.'/'.$entry;

            if (str_contains(strtolower($entry), strtolower($search))) { // add thing if it is in search query
                $files[] = [
                    'name' => $entry,
                    'mtime' => filemtime($full),
                    'size' => filesize($full),
                    'isfolder' => is_dir($full),
                    'showname' => $entry
                ];
            }
        }
        closedir($handle);
    }
}

// Natural alphabetical sort
usort($files, function($a, $b) {
    return strnatcasecmp($a['name'], $b['name']);
});

// Display rows
foreach ($files as $f) {
    $name = htmlspecialchars($f['name']);
    $display_name = $name;
    if ($f['mtime']) {
        $mtime = date("Y-m-d H:i", $f['mtime']);
    } else {
        $mtime = '';
    }
    $size = $f['size'];
    $mcv = null;

    if ($user === '') {
        $mcvdat = file_get_contents($base_path.'/info.mcv');
        $mcvarr = preg_split("/\r\n|\n|\r/", $mcvdat);
        $mcv = [];
        foreach ($mcvarr as $k) {
            if (substr($k, 0, 1) !== '#') {
                $waow = explode('=', $k, 2);
                $mcv[$waow[0]] = htmlspecialchars($waow[1]);
            }
        }
    }

    if ($f['isfolder']) {
        $size_display = "-";
        if (array_key_exists($f['name'], $mcv)) {
            $display_name = $mcv[$f['name']];
        } else if ($display_name === '*') {
            $display_name = htmlspecialchars('<all files>');
        }
        else {
            $display_name = '[Folder] '.$name; // placeholder
        }
    } else {
        $size_display = number_format($size) . " bytes";
        $display_name = htmlspecialchars($f['showname']);
        $ftypeicon = 'file.svg';

        $ext = '.'.strtolower(end(explode(".", $f['name'])));

        if (in_array($ext, $ftypes['doc'])) {
            $ftypeicon = 'doc.svg';
        } elseif (in_array($ext, $ftypes['aud'])) {
            $ftypeicon = 'aud.svg';
        } elseif (in_array($ext, $ftypes['arc'])) {
            $ftypeicon = 'arc.svg';
        } elseif (in_array($ext, $ftypes['vid'])) {
            $ftypeicon = 'vid.svg';
        } elseif (in_array($ext, $ftypes['img'])) {
            $ftypeicon = 'img.svg';
        }
        
    }

    echo "<tr class='item' data-name='".strtolower($name)."'>";
    if ($f['isfolder']) {
        echo "<td><a class=link href='/br.php?u=$name$theme'><img src='/bricons/folder.svg' class=icon>$display_name</a></td>";
    } else if ($user === '*') {
        echo "<td><a class=link href='/br/$name'><img src='/bricons/$ftypeicon' class=icon>$display_name</a></td>";
    } else {
        echo "<td><a class=link href='/br/$user/$name'><img src='/bricons/$ftypeicon' class=icon>$display_name</a></td>";
    }
    echo "<td>$mtime</td>";
    echo "<td>$size_display</td>";
    echo "</tr>";
}
?>
</tbody>
</table>
<?php
if ($tovr == 'none') {
  echo '<p>Theme Select: <a class=link href="?t=maricom-dawn">Maricom Dawn</a> | <a class=link href="?t=maricom">Maricom Day</a> | <a class=link href="?t=maricom-dusk">Maricom Dusk</a> | <a class=link href="?t=maricom-night">Maricom Night</a> | <a class=link href="?t=default">Standard</a> | <a class=link href="?t=dark">Standard (Dark)</a> | <a class=link href="?t=default-noicns">Classic</a> | <a class=link href="?t=bare">Minimal</a></p>';
}
?>
</div>
<script>
// remove server side object
const ssbutton = document.getElementById("search");
const thing = document.createElement("div");
thing.innerHTML = '<div id="search"><input type="text" class="searchbox" id="searchbox" placeholder="Search..." value=<?php $search = $_GET['q'] ?? ''; echo $search;?>> <button id="sbutton">Search</button></div>';
ssbutton.replaceWith(thing);

// client-side search filter
const search = document.getElementById("searchbox");
const button = document.getElementById("sbutton");
const items = document.querySelectorAll(".item");

button.addEventListener("click", () => {
    const q = search.value.toLowerCase();

    items.forEach(row => {
        row.style.display = row.dataset.name.includes(q) ? "" : "none";
    });
});
document.addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        const q = search.value.toLowerCase();

        items.forEach(row => {
            row.style.display = row.dataset.name.includes(q) ? "" : "none";
        });
    }
});
</script>

</body>
</html>

