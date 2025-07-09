import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Button,
  Card,
  CardHeader,
  CardBody,
  CardFooter,
  CardMedia,
  Input,
  Modal,
  ConfirmModal,
  useToast,
  ToastContainer,
  initializeThemeSystem,
  applyTheme,
  getCurrentTheme,
} from '../design-system';
import { 
  FiMail, 
  FiLock, 
  FiUser, 
  FiSearch, 
  FiPlus, 
  FiTrash2,
  FiEdit,
  FiCheck,
  FiX,
  FiSun,
  FiMoon,
} from 'react-icons/fi';

// Initialize design system on component mount
initializeThemeSystem();

export const DesignSystemDemo: React.FC = () => {
  const [theme, setTheme] = useState(getCurrentTheme());
  const [showModal, setShowModal] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    search: '',
  });
  const [inputErrors, setInputErrors] = useState<Record<string, string>>({});
  const { toasts, toast } = useToast();

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    applyTheme(newTheme);
    setTheme(newTheme);
    toast.info(`Switched to ${newTheme} mode`);
  };

  const handleInputChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [field]: e.target.value });
    // Clear error when user types
    if (inputErrors[field]) {
      setInputErrors({ ...inputErrors, [field]: '' });
    }
  };

  const validateForm = () => {
    const errors: Record<string, string> = {};
    if (!formData.email) errors.email = 'Email is required';
    if (!formData.password) errors.password = 'Password is required';
    if (formData.password && formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    }
    setInputErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = () => {
    if (validateForm()) {
      toast.success('Form submitted successfully!', {
        description: 'Your information has been saved.',
      });
      setShowModal(false);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: 'spring',
        stiffness: 100,
      },
    },
  };

  return (
    <motion.div
      className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="max-w-7xl mx-auto mb-12">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
              Premium Design System
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              Advanced components with delightful micro-interactions
            </p>
          </div>
          <Button
            variant="ghost"
            size="lg"
            icon={theme === 'light' ? <FiMoon /> : <FiSun />}
            onClick={toggleTheme}
          >
            {theme === 'light' ? 'Dark' : 'Light'} Mode
          </Button>
        </div>
      </motion.div>

      {/* Button Section */}
      <motion.section variants={itemVariants} className="max-w-7xl mx-auto mb-16">
        <h2 className="text-2xl font-semibold mb-6 text-gray-900 dark:text-white">Buttons</h2>
        <Card>
          <CardBody>
            <div className="space-y-6">
              {/* Button Variants */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Variants</h3>
                <div className="flex flex-wrap gap-3">
                  <Button variant="primary">Primary</Button>
                  <Button variant="secondary">Secondary</Button>
                  <Button variant="tertiary">Tertiary</Button>
                  <Button variant="ghost">Ghost</Button>
                  <Button variant="danger">Danger</Button>
                  <Button variant="success">Success</Button>
                </div>
              </div>

              {/* Button Sizes */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Sizes</h3>
                <div className="flex flex-wrap items-center gap-3">
                  <Button size="xs">Extra Small</Button>
                  <Button size="sm">Small</Button>
                  <Button size="md">Medium</Button>
                  <Button size="lg">Large</Button>
                  <Button size="xl">Extra Large</Button>
                </div>
              </div>

              {/* Button States */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">States & Effects</h3>
                <div className="flex flex-wrap gap-3">
                  <Button loading>Loading</Button>
                  <Button disabled>Disabled</Button>
                  <Button icon={<FiPlus />}>With Icon</Button>
                  <Button icon={<FiCheck />} iconPosition="right">Icon Right</Button>
                  <Button glow>Glow Effect</Button>
                  <Button pulse variant="danger">Pulse Effect</Button>
                </div>
              </div>
            </div>
          </CardBody>
        </Card>
      </motion.section>

      {/* Input Section */}
      <motion.section variants={itemVariants} className="max-w-7xl mx-auto mb-16">
        <h2 className="text-2xl font-semibold mb-6 text-gray-900 dark:text-white">Inputs</h2>
        <Card>
          <CardBody>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Input
                label="Email Address"
                type="email"
                placeholder="Enter your email"
                icon={<FiMail />}
                value={formData.email}
                onChange={handleInputChange('email')}
                error={inputErrors.email}
              />
              <Input
                label="Password"
                type="password"
                placeholder="Enter your password"
                icon={<FiLock />}
                value={formData.password}
                onChange={handleInputChange('password')}
                error={inputErrors.password}
                clearable
              />
              <Input
                variant="filled"
                label="Full Name"
                placeholder="John Doe"
                icon={<FiUser />}
                value={formData.name}
                onChange={handleInputChange('name')}
                helper="Enter your full legal name"
              />
              <Input
                variant="flushed"
                label="Search"
                placeholder="Search for anything..."
                icon={<FiSearch />}
                iconPosition="right"
                value={formData.search}
                onChange={handleInputChange('search')}
              />
              <Input
                label="Success State"
                value="Valid input"
                success="Great! This looks good."
                readOnly
              />
              <Input
                label="Loading State"
                placeholder="Checking availability..."
                loading
              />
            </div>
          </CardBody>
        </Card>
      </motion.section>

      {/* Card Section */}
      <motion.section variants={itemVariants} className="max-w-7xl mx-auto mb-16">
        <h2 className="text-2xl font-semibold mb-6 text-gray-900 dark:text-white">Cards</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card variant="default" hover>
            <CardHeader
              title="Default Card"
              subtitle="With hover effect"
            />
            <CardBody>
              <p className="text-gray-600 dark:text-gray-400">
                This is a default card with hover animation. It lifts up slightly when you hover over it.
              </p>
            </CardBody>
            <CardFooter>
              <Button variant="ghost" size="sm">Learn More</Button>
            </CardFooter>
          </Card>

          <Card variant="elevated" hover glow>
            <CardMedia
              src="https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=400&h=200&fit=crop"
              height={200}
            />
            <CardHeader
              title="Elevated Card"
              subtitle="With glow effect"
            />
            <CardBody>
              <p className="text-gray-600 dark:text-gray-400">
                This card has elevation and a beautiful glow effect on hover.
              </p>
            </CardBody>
            <CardFooter>
              <div className="flex gap-2 w-full">
                <Button variant="primary" size="sm" fullWidth>
                  Get Started
                </Button>
              </div>
            </CardFooter>
          </Card>

          <Card variant="interactive" hover>
            <CardHeader
              title="Interactive Card"
              subtitle="Click anywhere"
              action={
                <Button
                  variant="ghost"
                  size="sm"
                  icon={<FiEdit />}
                  onClick={(e) => {
                    e.stopPropagation();
                    toast.info('Edit clicked!');
                  }}
                />
              }
            />
            <CardBody>
              <p className="text-gray-600 dark:text-gray-400">
                This entire card is clickable with spring animations.
              </p>
            </CardBody>
          </Card>
        </div>
      </motion.section>

      {/* Toast Section */}
      <motion.section variants={itemVariants} className="max-w-7xl mx-auto mb-16">
        <h2 className="text-2xl font-semibold mb-6 text-gray-900 dark:text-white">Toasts</h2>
        <Card>
          <CardBody>
            <div className="flex flex-wrap gap-3">
              <Button
                variant="primary"
                onClick={() => toast.info('This is an info toast')}
              >
                Show Info
              </Button>
              <Button
                variant="success"
                onClick={() => toast.success('Operation completed!', {
                  description: 'Your changes have been saved.',
                })}
              >
                Show Success
              </Button>
              <Button
                variant="tertiary"
                onClick={() => toast.warning('Warning!', {
                  description: 'Please review your input.',
                })}
              >
                Show Warning
              </Button>
              <Button
                variant="danger"
                onClick={() => toast.error('Error occurred!', {
                  description: 'Something went wrong. Please try again.',
                })}
              >
                Show Error
              </Button>
              <Button
                variant="secondary"
                onClick={() => toast.success('Action required', {
                  description: 'Click the action button to proceed.',
                  action: {
                    label: 'Undo',
                    onClick: () => toast.info('Action undone!'),
                  },
                })}
              >
                With Action
              </Button>
            </div>
          </CardBody>
        </Card>
      </motion.section>

      {/* Modal Section */}
      <motion.section variants={itemVariants} className="max-w-7xl mx-auto mb-16">
        <h2 className="text-2xl font-semibold mb-6 text-gray-900 dark:text-white">Modals</h2>
        <Card>
          <CardBody>
            <div className="flex flex-wrap gap-3">
              <Button onClick={() => setShowModal(true)}>
                Open Modal
              </Button>
              <Button
                variant="danger"
                icon={<FiTrash2 />}
                onClick={() => setShowConfirm(true)}
              >
                Delete Item
              </Button>
            </div>
          </CardBody>
        </Card>
      </motion.section>

      {/* Modals */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="Create New Account"
        description="Fill in the information below to get started"
        size="md"
        footer={
          <div className="flex gap-3">
            <Button variant="ghost" onClick={() => setShowModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleSubmit}>
              Create Account
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <Input
            label="Email"
            type="email"
            icon={<FiMail />}
            value={formData.email}
            onChange={handleInputChange('email')}
            error={inputErrors.email}
          />
          <Input
            label="Password"
            type="password"
            icon={<FiLock />}
            value={formData.password}
            onChange={handleInputChange('password')}
            error={inputErrors.password}
          />
        </div>
      </Modal>

      <ConfirmModal
        isOpen={showConfirm}
        onClose={() => setShowConfirm(false)}
        title="Delete Item"
        message="Are you sure you want to delete this item? This action cannot be undone."
        confirmLabel="Delete"
        confirmVariant="danger"
        onConfirm={() => {
          toast.success('Item deleted successfully!');
        }}
      />

      {/* Toast Container */}
      <ToastContainer toasts={toasts} position="bottom-right" />
    </motion.div>
  );
};