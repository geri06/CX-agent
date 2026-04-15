import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { fetchCollection } from '../../lib/api';
import RestaurantCard from './RestaurantCard';
import InvoiceTable from './InvoiceTable';
import IngredientTable from './IngredientTable';
import RecipeCard from './RecipeCard';
import { Loader2 } from 'lucide-react';

const TITLES = {
  restaurants: 'Restaurants',
  invoices: 'Invoices',
  ingredients: 'Ingredients',
  recipes: 'Recipes',
};

export default function DataView({ activeCollection }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchCollection(activeCollection)
      .then((items) => {
        if (!cancelled) {
          setData(items);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, [activeCollection]);

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-64">
          <Loader2 size={24} className="animate-spin text-[var(--color-accent)]" />
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <p className="text-[var(--color-danger)] text-sm font-medium mb-1">Failed to load data</p>
            <p className="text-[var(--color-text-tertiary)] text-xs">{error}</p>
            <p className="text-[var(--color-text-tertiary)] text-xs mt-2">Make sure the backend is running on port 8000</p>
          </div>
        </div>
      );
    }

    switch (activeCollection) {
      case 'restaurants':
        return (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {data.map((r, i) => (
              <motion.div
                key={r.restaurant_id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05, duration: 0.3 }}
              >
                <RestaurantCard restaurant={r} />
              </motion.div>
            ))}
          </div>
        );
      case 'invoices':
        return <InvoiceTable invoices={data} />;
      case 'ingredients':
        return <IngredientTable ingredients={data} />;
      case 'recipes':
        return (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {data.map((r, i) => (
              <motion.div
                key={r.recipe_id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05, duration: 0.3 }}
              >
                <RecipeCard recipe={r} />
              </motion.div>
            ))}
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-full bg-[var(--color-bg-primary)]">
      {/* Header Area */}
      <div className="px-12 py-8 border-b border-[var(--color-border)] bg-white shrink-0 shadow-[0_1px_2px_rgba(0,0,0,0.02)] z-10 relative">
        <h2 className="text-2xl font-semibold text-[var(--color-text-primary)] tracking-tight">
          {TITLES[activeCollection]}
        </h2>
        <p className="text-sm text-[var(--color-text-tertiary)] mt-1.5">
          Mock database — {data.length} record{data.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto w-full">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeCollection}
            initial={{ opacity: 0, x: 8 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -8 }}
            transition={{ duration: 0.2 }}
            className="p-12 max-w-7xl mx-auto w-full"
          >
            {renderContent()}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
