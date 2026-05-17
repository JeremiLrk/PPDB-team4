// Shared UI building block for ItemCard.

import styles from "@/style/common/Panel.module.css";

/**
 * ItemCard — generic line-box for lists.
 *
 * Renders <li> with style .listItem (flex, space-between).
 * Arbitrary content is passed inside via children.
 *
 * Props:
 * children — content of the box
 * className — additional CSS class (optional)
 * style — inline styles (optional)
 */
export default function ItemCard({ children, className, style }) {
    /*
     Renders one shared list-row container.
    */
    const cls = [styles.listItem, className].filter(Boolean).join(" ");

    return (
        <li className={cls} style={style}>
            {children}
        </li>
    );
}
