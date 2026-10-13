# Проверка idmap2: пригодны ли статические RRO в /vendor/overlay — 12 октября 2026

Только чтение/временные файлы в `/data/local/tmp/beam-idmap-test` (удалены). Play 6 / v1.7.116. Журнал: [IDMAP-TEST.log](IDMAP-TEST.log).

## Опыт

Для пяти наших overlay (settings→newsettings, systemui→systemui, atmosphere, manager, frameworkpower→android) создавался idmap без `--ignore-overlayable` с разными политиками и считалось число сопоставленных ресурсов (`idmap2 dump`).

| Политика | Результат |
|---|---|
| `--ignore-overlayable --policy public` (как сейчас) | settings 231, systemui 212, atmosphere 131, manager 103, framework 2 |
| `--policy public` (как у обычного overlay из /data) | **rc=1, «no resources were overlaid»** — ничего |
| `vendor`, `system`, `product`, `odm`, `oem`, `signature` | **те же 231 / 212 / 131 / 103 / 2** — полностью |
| `actor` | rc=1, ничего |

Цели не объявляют `<overlayable>` (счёт строк в resources.arsc = 0). Для политик, соответствующих разделу, все ресурсы доступны для замены.

## Вывод

Причина, по которой сейчас нужен `--ignore-overlayable`, — политика `public`, которую получает overlay, установленный в /data. Overlay, лежащий в разделе (vendor/system/product), получил бы политику раздела, и idmap строился бы полностью без обхода.

## Не проверено

- В прошивке нет ни одного предустановленного overlay: каталоги `/vendor/overlay`, `/system/overlay`, `/product/overlay` отсутствуют. Сканирует ли PMS `/vendor/overlay` в этой сборке и включит ли OMS статический overlay, не наблюдалось.
- Нужен манифест с `android:isStatic="true"` и приоритетом; ограничения на раздел цели (vendor-overlay и цели в /system) и требования к подписи для предустановленных overlay не проверялись.
- Запись файлов в vendor (новый каталог и 14 файлов) сложнее правки одной строки: нужен свободный inode и блоки (в vendor 1792 inode, использовано 1660, свободно 132; блоков ~70 МБ).
