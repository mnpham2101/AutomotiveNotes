# FPT Theme Colors

Extracted from `Template for Teams - Hackathon 2026.pptx` — theme color scheme **"Custom 12"** (`ppt/theme/theme1.xml`).

## Primary theme colors

| Color      | Hex       | RGB                | PPTX theme slot | Suggested usage                     |
| ---------- | --------- | ------------------ | --------------- | ----------------------------------- |
| Orange     | `#F37021` | rgb(243, 112, 33)  | accent1, hlink  | Primary accent (FPT orange)         |
| Green      | `#50B848` | rgb(80, 184, 72)   | accent2         | Secondary accent (FPT green)        |
| Light Blue | `#33B2C1` | rgb(51, 178, 193)  | accent4         | Tertiary accent / highlights        |
| Dark Blue  | `#034EA2` | rgb(3, 78, 162)    | accent3         | Headings / primary brand blue (FPT blue) |

## Supporting colors (same scheme)

| Color     | Hex       | PPTX theme slot | Notes                    |
| --------- | --------- | --------------- | ------------------------ |
| Navy      | `#19226D` | accent5         | Extra-dark blue variant  |
| Near-black| `#080808` | dk1             | Body text                |
| Dark Gray | `#4D4D4D` | dk2             | Secondary text           |
| Gray      | `#AEABAB` | accent6         | Borders / muted elements |
| White     | `#FFFFFF` | lt1, lt2        | Background               |

## CSS variables

```css
:root {
  --fpt-orange:     #F37021;
  --fpt-green:      #50B848;
  --fpt-light-blue: #33B2C1;
  --fpt-dark-blue:  #034EA2;
  --fpt-navy:       #19226D;
  --fpt-text:       #080808;
  --fpt-gray:       #4D4D4D;
  --fpt-border:     #AEABAB;
  --fpt-bg:         #FFFFFF;
}
```

## Related assets

- FPT logo (full color, transparent background): [fpt-logo.png](fpt-logo.png) — extracted from the same PPTX (`ppt/media/image7.png`, cropped to content).
