<!doctype html>
<html>
<head>
<title>Billion Reservoir SSD</title>
<style>
body {
    font-family: monospace;
    background: #fff;
    margin: 20px;
    width: 100vw;            /* fills viewport horizontally */
    overflow-x: hidden;      /* prevents overflow scrollbars */
}

table {
    border-collapse: collapse;
    width: 100%;             /* table matches viewport */
    table-layout: fixed;     /* forces wrapping + stable columns */
}

td, th {
    padding: 4px;
    border-bottom: 1px solid #ddd;
    font-size: 14px;
    word-wrap: break-word;   /* wrap long file names */
    overflow-wrap: break-word;
}

/* First column (Name) gets flexible wrapping space */
td:nth-child(1), th:nth-child(1) {
    width: 40%;              /* flexible but mostly name column */
}

/* Other columns stay aligned and do not shrink too small */
td:nth-child(2), th:nth-child(2),
td:nth-child(3), th:nth-child(3),
td:nth-child(4), th:nth-child(4) {
    width: 20%;
    white-space: nowrap;     /* prevents timestamps/sizes from wrapping */
}
    a {
        color: #00f;
        text-decoration: none;
    }

    a:hover {
        text-decoration: underline;
    }
</style>
</head>

<body>

<h1><a href="/br.php"><font color="black">Billion Reservoir SSD</font></a></h1>

<form action="/br.php" method="get" id="serversidesearch">
    <input type="hidden" name="u" value="<?php $user = $_GET['u'] ?? ''; echo $user;?>" />
    <input type="text" name="q" class="searchbox" placeholder="Search..." value=<?php $search = $_GET['q'] ?? ''; echo $search;?>>
    <button type="submit">Search</button>
</form>

<table>
<thead>
<tr>
    <th>Name</th>
    <th>Last modified</th>
    <th>Size</th>
    <th>Description</th>
</tr>
</thead>

<tbody id="filelist">
<?php
$base_path = '/var/www/html/br/'; // base folder to search
$user = $_GET['u'] ?? '';

$path = $base_path.'/'.$user;
$files = [];
$search = $_GET['q'] ?? '';

if ($user === '') {
    $files[] = [
        'name' => '*',
        'mtime' => 0,
        'size' => '-',
        'desc' => '', // blank description (Apache usually leaves blank)
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

                    if (str_contains(strtolower($entry), strtolower($search))) { // add thing if it is in search query
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
                    'desc' => '', // blank description (Apache usually leaves blank)
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
    $mtime = date("Y-m-d H:i", $f['mtime']);
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
    }

    echo "<tr class='item' data-name='".strtolower($name)."'>";
    if ($f['isfolder']) {
        echo "<td><a href='/br.php?u=$name'>$display_name</a></td>";
    } else if ($user === '*') {
        echo "<td><a href='/br/$name'>$display_name</a></td>";
    } else {
        echo "<td><a href='/br/$user/$name'>$display_name</a></td>";
    }
    echo "<td>$mtime</td>";
    echo "<td>$size_display</td>";
    echo "<td></td>";
    echo "</tr>";
}
?>
</tbody>
</table>

<script>
// remove server side object
const ssbutton = document.getElementById("serversidesearch");
const thing = document.createElement("div");
thing.innerHTML = '<input type="text" class="searchbox" id="search" placeholder="Search..." value=<?php $search = $_GET['q'] ?? ''; echo $search;?>>';
ssbutton.replaceWith(thing);

// client-side search filter
const search = document.getElementById("search");
const items = document.querySelectorAll(".item");

search.addEventListener("input", () => {
    const q = search.value.toLowerCase();

    items.forEach(row => {
        row.style.display = row.dataset.name.includes(q) ? "" : "none";
    });
});
</script>

</body>
</html>

