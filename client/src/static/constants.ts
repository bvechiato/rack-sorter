export const SIZES: { value: string; label: string }[] = [
  { value: '1226', label: 'XXXS / UK 0' },
  { value: '102', label: 'XXS / UK 2' },
  { value: '2', label: 'XS / UK 4-6' },
  { value: '3', label: 'S / UK 8-10' },
  { value: '4', label: 'M / UK 12-14' },
  { value: '5', label: 'L / UK 16-18' },
  { value: '6', label: 'XL / UK 20-22' },
  { value: '7', label: 'XXL / UK 24-26' },
  { value: '310', label: 'XXXL / UK 28-30' },
  { value: '311', label: '4XL / UK 32-34' },
  { value: '312', label: '5XL / UK 36-38' },
];

export const CATEGORIES: string[] = [
  'See all',
  'Outerwear',
  'Jumpers & sweaters',
  'Suits & blazers',
  'Dresses',
  'Skirts',
  'Skorts',
  'Tops & t-shirts',
  'Jeans',
  'Trousers & leggings',
  'Shorts & cropped trousers',
  'Jumpsuits & playsuits',
  'Swimwear',
  'Lingerie & nightwear',
  'Maternity clothes',
  'Activewear',
  'Shoes',
  'Bags',
];

export const COLORS: { name: string; class: string }[] = [
  { name: 'Black', class: 'c-black' },
  { name: 'Grey', class: 'c-grey' },
  { name: 'White', class: 'c-white' },
  { name: 'Cream', class: 'c-cream' },
  { name: 'Orange', class: 'c-orange' },
  { name: 'Red', class: 'c-red' },
  { name: 'Pink', class: 'c-pink' },
  { name: 'Purple', class: 'c-purple' },
  { name: 'Blue', class: 'c-blue' },
  { name: 'Turquoise', class: 'c-turquoise' },
  { name: 'Green', class: 'c-green' },
  { name: 'Brown', class: 'c-brown' },
  { name: 'Yellow', class: 'c-yellow' },
  { name: 'Multi', class: 'c-multi' },
  { name: 'Clear', class: 'c-clear' },
];

export const CONDITION_OPTIONS: { value: string; label: string }[] = [
  { value: '6', label: 'New with tags' },
  { value: '1', label: 'New without tags' },
  { value: '2', label: 'Very Good' },
  { value: '3', label: 'Good' },
];

/** Fixed trait vocabulary. Must mirror `Trait` in `server/service/traits.py`. */
export type Trait = 'sleeves' | 'neckline' | 'length' | 'pattern' | 'fit' | 'material';

export interface TraitOption {
  key: Trait;
  label: string;
  /** Axes whose reliability is still being evaluated; rendered with a hint. */
  beta?: boolean;
}

export const TRAITS: TraitOption[] = [
  { key: 'sleeves', label: 'Sleeves' },
  { key: 'neckline', label: 'Neckline' },
  { key: 'length', label: 'Length' },
  { key: 'pattern', label: 'Pattern' },
  { key: 'fit', label: 'Fit' },
  { key: 'material', label: 'Material', beta: true },
];
